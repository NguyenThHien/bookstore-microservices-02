from django.shortcuts import render, redirect
from django.http import JsonResponse
from functools import wraps
import requests

CUSTOMER_SERVICE_URL = "http://customer-service:8000"
BOOK_SERVICE_URL = "http://book-service:8000"
CART_SERVICE_URL = "http://cart-service:8000"
ORDER_SERVICE_URL = "http://order-service:8000"
PAY_SERVICE_URL = "http://pay-service:8000"
SHIP_SERVICE_URL = "http://ship-service:8000"
COMMENT_RATE_SERVICE_URL = "http://comment-rate-service:8000"
STAFF_SERVICE_URL = "http://staff-service:8000"
CATALOG_SERVICE_URL = "http://catalog-service:8000"

def _safe_json(response):
    try:
        return response.json()
    except Exception:
        return None


def _friendly_non_json_error(response):
    text = (response.text or "").strip().replace("\r", "")
    snippet = text[:200]
    if len(text) > 200:
        snippet += "..."
    return f"Lỗi từ dịch vụ (HTTP {response.status_code}): {snippet or '(no body)'}"


def _unwrap_books(data):
    """Book-service returns paginated {total, page, limit, results} or plain list."""
    if isinstance(data, dict):
        return data.get('results', [])
    if isinstance(data, list):
        return data
    return []


def _sync_staff_flags_from_staff_service(request):
    """Nếu email tồn tại trong staff-service thì set is_staff/is_admin vào session."""
    email = request.session.get("customer_email")
    if not email:
        return
    try:
        staff_resp = requests.get(
            f"{STAFF_SERVICE_URL}/staff/",
            params={"email": email},
            timeout=5,
        )
        if staff_resp.status_code == 200:
            staff_list = staff_resp.json() or []
            if isinstance(staff_list, list) and staff_list:
                request.session["is_staff"] = True
                request.session["is_admin"] = staff_list[0].get("role") == "admin"
                request.session.modified = True
    except Exception:
        pass

def _load_categories():
    """Tải danh mục từ catalog-service, trả về list dict [{id, name, subcategories: [...]}, ...]."""
    try:
        resp = requests.get(f"{CATALOG_SERVICE_URL}/categories/", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _ensure_default_categories():
    """Seed các danh mục mặc định (theo UI) nếu chưa có."""
    defaults = [
        {"name": "Lập trình", "description": "Sách lập trình, công nghệ", "is_active": True},
        {"name": "Kỹ năng sống", "description": "Kỹ năng, phát triển bản thân", "is_active": True},
        {"name": "Tiểu thuyết", "description": "Văn học, tiểu thuyết", "is_active": True},
        {"name": "Tài chính", "description": "Tài chính, đầu tư", "is_active": True},
        {"name": "Tâm lý học", "description": "Tâm lý, hành vi", "is_active": True},
        {"name": "Lịch sử", "description": "Lịch sử, văn hóa", "is_active": True},
    ]

    existing = _load_categories()
    existing_names = {str(c.get("name", "")).strip().lower() for c in existing}

    for c in defaults:
        if c["name"].strip().lower() in existing_names:
            continue
        try:
            requests.post(f"{CATALOG_SERVICE_URL}/categories/", json=c, timeout=5)
        except Exception:
            pass


# Decorator: customer must be logged in
def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'customer_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# Decorator: must be staff or admin (checked from session, not extra HTTP call)
def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'customer_id' not in request.session:
            return redirect('login')

        # Ưu tiên check Staff-service theo email, không phụ thuộc flag trong customer
        email = request.session.get('customer_email')
        is_staff = request.session.get('is_staff', False)
        is_admin = request.session.get('is_admin', False)

        if email and not (is_staff or is_admin):
            try:
                staff_resp = requests.get(
                    f"{STAFF_SERVICE_URL}/staff/",
                    params={"email": email},
                    timeout=5,
                )
                if staff_resp.status_code == 200:
                    staff_list = staff_resp.json() or []
                    if isinstance(staff_list, list) and staff_list:
                        # Có staff record → gán quyền staff vào session
                        request.session['is_staff'] = True
                        # Admin role trong staff-service map sang is_admin
                        if staff_list[0].get('role') == 'admin':
                            request.session['is_admin'] = True
                        request.session.modified = True
                        is_staff = True
                        is_admin = request.session.get('is_admin', False)
            except Exception:
                # Nếu staff-service lỗi thì fallback sang flags hiện có
                pass

        if not (is_staff or is_admin):
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


# Trang chủ
def home(request):
    try:
        response = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
        books = _unwrap_books(response.json())[:6] if response.status_code == 200 else []
    except Exception:
        books = []
    return render(request, "home.html", {"books": books})


# Tìm kiếm sách
def search_books(request):
    query = request.GET.get("q", "")
    try:
        response = requests.get(f"{BOOK_SERVICE_URL}/books/search/?q={query}", timeout=5)
        if response.status_code == 200:
            books = response.json()
            if isinstance(books, dict):
                books = books.get('results', [])
        else:
            # Fallback: get all and filter client-side
            response2 = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
            books = _unwrap_books(response2.json()) if response2.status_code == 200 else []
            if query:
                books = [b for b in books if
                         query.lower() in b.get('title', '').lower() or
                         query.lower() in b.get('author', '').lower()]
    except Exception:
        books = []

    return render(request, "search.html", {"books": books, "query": query})


# Chi tiết sách
def book_detail(request, book_id):
    try:
        response = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
        book = response.json() if response.status_code == 200 else None
    except Exception:
        book = None
    try:
        rating_response = requests.get(f"{COMMENT_RATE_SERVICE_URL}/books/{book_id}/ratings/", timeout=5)
        rating_data = rating_response.json() if rating_response.status_code == 200 else {"ratings": [], "average": 0}
    except Exception:
        rating_data = {"ratings": [], "average": 0}

    return render(request, "book_detail.html", {
        "book": book,
        "ratings": rating_data.get("ratings", []),
        "avg_rating": rating_data.get("average", 0),
    })


@login_required
def rate_book(request, book_id):
    if request.method != "POST":
        return redirect("book_detail", book_id=book_id)

    customer_id = request.session.get("customer_id")
    rating = request.POST.get("rating")
    comment = request.POST.get("comment", "")

    try:
        rating_int = int(rating)
    except Exception:
        rating_int = None

    if not rating_int or rating_int < 1 or rating_int > 5:
        return redirect("book_detail", book_id=book_id)

    try:
        # Unique constraint in service: (book_id, customer_id)
        # If already exists, update via PUT/PATCH is possible but not exposed easily here.
        # We attempt create; on 400, we silently ignore to avoid breaking flow.
        requests.post(
            f"{COMMENT_RATE_SERVICE_URL}/ratings/",
            json={
                "book_id": int(book_id),
                "customer_id": int(customer_id),
                "rating": rating_int,
                "comment": comment,
            },
            timeout=5
        )
    except Exception:
        pass

    return redirect("book_detail", book_id=book_id)


# Đăng ký khách hàng
def register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not all([name, email, password]):
            return render(request, "register.html", {"error": "Vui lòng điền đầy đủ thông tin"})

        try:
            response = requests.post(
                f"{CUSTOMER_SERVICE_URL}/customers/",
                json={"name": name, "email": email, "password": password},
                timeout=5
            )
            if response.status_code in [200, 201]:
                customer = _safe_json(response)
                if not isinstance(customer, dict):
                    return render(request, "register.html", {"error": _friendly_non_json_error(response)})
                _set_session(request, customer)
                return redirect("books")
            else:
                err = _safe_json(response)
                if err is None:
                    msg = _friendly_non_json_error(response)
                else:
                    msg = err.get('email', [err])[0] if isinstance(err, dict) else str(err)
                return render(request, "register.html", {"error": msg})
        except Exception as e:
            return render(request, "register.html", {"error": f"Không thể kết nối: {e}"})

    return render(request, "register.html")


# Đăng nhập
def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not all([email, password]):
            return render(request, "login.html", {"error": "Vui lòng nhập email và mật khẩu"})

        try:
            response = requests.post(
                f"{CUSTOMER_SERVICE_URL}/customers/verify-password/",
                json={"email": email, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                customer = _safe_json(response)
                if not isinstance(customer, dict):
                    return render(request, "login.html", {"error": _friendly_non_json_error(response)})
                _set_session(request, customer)
                # Sync staff/admin from staff-service (source of truth)
                _sync_staff_flags_from_staff_service(request)
                # Redirect admin/staff to dashboard, others to books
                if request.session.get('is_admin') or request.session.get('is_staff'):
                    return redirect("admin_dashboard")
                return redirect("books")
            else:
                return render(request, "login.html", {"error": "Email hoặc mật khẩu không đúng"})
        except Exception as e:
            return render(request, "login.html", {"error": f"Không thể kết nối: {e}"})

    return render(request, "login.html")


def _set_session(request, customer):
    """Store customer info in session."""
    request.session['customer_id'] = customer.get('id')
    request.session['customer_name'] = customer.get('name', '')
    request.session['customer_email'] = customer.get('email', '')
    request.session['is_staff'] = customer.get('is_staff', False)
    request.session['is_admin'] = customer.get('is_admin', False)
    request.session.modified = True


# Đăng xuất
def logout(request):
    request.session.flush()
    return redirect("home")


# Danh sách sách
def books(request):
    try:
        response = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
        book_list = _unwrap_books(response.json()) if response.status_code == 200 else []
    except Exception:
        book_list = []

    customer_id = request.session.get('customer_id')
    return render(request, "books.html", {"books": book_list, "customer_id": customer_id})


# Thêm sách (Staff only)
@staff_required
def add_book(request):
    if request.method == "POST":
        title = request.POST.get("title")
        author = request.POST.get("author")
        price = request.POST.get("price")
        stock = request.POST.get("stock")
        description = request.POST.get("description", "")
        category = request.POST.get("category", "")
        publisher = request.POST.get("publisher") or ""
        pages = request.POST.get("pages") or None

        try:
            response = requests.post(
                f"{BOOK_SERVICE_URL}/books/",
                json={
                    "title": title,
                    "author": author,
                    "price": float(price),
                    "stock": int(stock),
                    "description": description,
                    "category": category,
                    "publisher": publisher or None,
                    "pages": int(pages) if pages else None,
                },
                timeout=5
            )
            if response.status_code in [200, 201]:
                return redirect("admin_dashboard")
            else:
                # Hiển thị lỗi chi tiết từ book-service nếu có
                data = _safe_json(response)
                if isinstance(data, dict):
                    # Ghép các message validation lại
                    messages = []
                    for field, msg in data.items():
                        if isinstance(msg, list):
                            msg = "; ".join(str(m) for m in msg)
                        messages.append(f"{field}: {msg}")
                    error_text = " ; ".join(messages) or "Không thể thêm sách"
                else:
                    error_text = _friendly_non_json_error(response)
                # Lấy lại danh mục để render form
                categories = _load_categories()
                return render(
                    request,
                    "add_book.html",
                    {"error": error_text, "post": request.POST, "categories": categories},
                )
        except Exception as e:
            categories = _load_categories()
            return render(request, "add_book.html", {"error": str(e), "post": request.POST, "categories": categories})

    categories = _load_categories()
    return render(request, "add_book.html", {"categories": categories})


# Xem giỏ hàng
@login_required
def cart(request):
    customer_id = request.session.get('customer_id')
    try:
        response = requests.get(f"{CART_SERVICE_URL}/carts/{customer_id}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # ViewCart returns a list; GetCart returns an object with items field
            items = data if isinstance(data, list) else data.get('items', [])
        else:
            items = []
    except Exception:
        items = []

    # Enrich cart items with book info for UI
    enriched_items = []
    for item in items:
        book_id = item.get("book_id")
        book = {}
        try:
            if book_id is not None:
                book_resp = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
                if book_resp.status_code == 200:
                    book = book_resp.json() or {}
        except Exception:
            book = {}

        quantity = int(item.get("quantity", 1) or 1)
        price = float(item.get("price", 0) or 0)
        enriched_items.append({
            **item,
            "title": book.get("title") or item.get("title") or "Sách",
            "author": book.get("author") or "",
            "stock": book.get("stock"),
            "line_total": price * quantity,
        })

    total = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in enriched_items)
    return render(request, "cart.html", {
        "items": enriched_items,
        "customer_id": customer_id,
        "total": total,
    })


@login_required
def update_cart_item(request, item_id):
    if request.method != "POST":
        return redirect("cart")

    try:
        quantity = int(request.POST.get("quantity", 1))
    except Exception:
        quantity = 1

    try:
        requests.put(
            f"{CART_SERVICE_URL}/cart-items/{item_id}/",
            json={"quantity": quantity},
            timeout=5
        )
    except Exception:
        pass

    return redirect("cart")


@login_required
def delete_cart_item(request, item_id):
    if request.method != "POST":
        return redirect("cart")

    try:
        requests.delete(f"{CART_SERVICE_URL}/cart-items/{item_id}/delete/", timeout=5)
    except Exception:
        pass

    return redirect("cart")


# Thêm sách vào giỏ hàng
@login_required
def add_to_cart(request):
    if request.method == "POST":
        customer_id = request.session.get('customer_id')
        book_id = request.POST.get("book_id")
        quantity = int(request.POST.get("quantity", 1))

        if not customer_id:
            return redirect('login')

        try:
            # Get or create cart
            cart_response = requests.get(
                f"{CART_SERVICE_URL}/carts/get/{customer_id}/",
                timeout=5
            )
            if cart_response.status_code == 200:
                cart_id = cart_response.json().get("id")
            else:
                # Create cart
                create_response = requests.post(
                    f"{CART_SERVICE_URL}/carts/",
                    json={"customer_id": customer_id},
                    timeout=5
                )
                cart_id = create_response.json().get("id") if create_response.status_code in [200, 201] else None

            if cart_id:
                requests.post(
                    f"{CART_SERVICE_URL}/cart-items/",
                    json={"cart": cart_id, "book_id": int(book_id), "quantity": quantity},
                    timeout=5
                )
        except Exception:
            pass

    return redirect("cart")


# Đặt hàng
@login_required
def place_order(request):
    customer_id = request.session.get('customer_id')

    if request.method == "POST":
        address = request.POST.get("address", "")
        payment_method = request.POST.get("payment_method", "card")
        shipping_method = request.POST.get("shipping_method", "standard")

        try:
            cart_response = requests.get(f"{CART_SERVICE_URL}/carts/{customer_id}/", timeout=5)
            if cart_response.status_code != 200:
                return redirect("cart")
            data = cart_response.json()
            items = data if isinstance(data, list) else data.get('items', [])

            if not items:
                return redirect("cart")

            total_amount = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in items)

            # Create order
            order_response = requests.post(
                f"{ORDER_SERVICE_URL}/orders/",
                json={
                    "customer_id": customer_id,
                    "total_amount": total_amount,
                    "items": items,
                    "shipping_address": address,
                    "payment_method": payment_method,
                    "shipping_method": shipping_method,
                },
                timeout=5
            )

            if order_response.status_code in [200, 201]:
                order = order_response.json()
                order_id = order.get('id')

                return redirect(f"/order-status/{order_id}/")
        except Exception as e:
            return render(request, "checkout.html", {"error": str(e), "items": [], "total_amount": 0})

        return redirect("cart")

    try:
        cart_response = requests.get(f"{CART_SERVICE_URL}/carts/{customer_id}/", timeout=5)
        data = cart_response.json() if cart_response.status_code == 200 else []
        items = data if isinstance(data, list) else data.get('items', [])
    except Exception:
        items = []

    total_amount = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in items)

    return render(request, "checkout.html", {
        "items": items,
        "customer_id": customer_id,
        "total_amount": total_amount
    })


# Trạng thái đơn hàng
def order_status(request, order_id):
    try:
        order_response = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}/", timeout=5)
        order = order_response.json() if order_response.status_code == 200 else None
    except Exception:
        order = None

    try:
        payment_response = requests.get(f"{PAY_SERVICE_URL}/orders/{order_id}/payment/", timeout=5)
        payments = payment_response.json() if payment_response.status_code == 200 else []
    except Exception:
        payments = []

    try:
        shipment_response = requests.get(f"{SHIP_SERVICE_URL}/orders/{order_id}/shipment/", timeout=5)
        shipments = shipment_response.json() if shipment_response.status_code == 200 else []
    except Exception:
        shipments = []

    return render(request, "order_status.html", {
        "order": order,
        "payments": payments,
        "shipments": shipments
    })


# Đơn hàng của khách
@login_required
def customer_orders(request):
    customer_id = request.session.get('customer_id')
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/orders/customer/{customer_id}/", timeout=5)
        data = response.json() if response.status_code == 200 else []
        if isinstance(data, dict):
            # handle paginated or error dicts
            data = data.get("results", [])
        orders = data if isinstance(data, list) else []
        # Filter out malformed rows missing id (prevents NoReverseMatch)
        orders = [o for o in orders if isinstance(o, dict) and o.get("id")]
    except Exception:
        orders = []
    return render(request, "customer_orders.html", {"orders": orders})


# Hồ sơ khách hàng
@login_required
def profile(request):
    customer_id = request.session.get('customer_id')
    try:
        response = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/", timeout=5)
        customer = response.json() if response.status_code == 200 else None
    except Exception:
        customer = None
    return render(request, "profile.html", {"customer": customer})


# Admin Dashboard
@staff_required
def admin_dashboard(request):
    try:
        orders_response = requests.get(f"{ORDER_SERVICE_URL}/orders/", timeout=5)
        orders = orders_response.json() if orders_response.status_code == 200 else []
        if isinstance(orders, dict):
            orders = orders.get('results', [])
    except Exception:
        orders = []

    try:
        customers_response = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/", timeout=5)
        customers = customers_response.json() if customers_response.status_code == 200 else []
    except Exception:
        customers = []

    try:
        books_response = requests.get(f"{BOOK_SERVICE_URL}/books/", timeout=5)
        books = _unwrap_books(books_response.json()) if books_response.status_code == 200 else []
    except Exception:
        books = []

    categories = _load_categories()
    active_categories = [c for c in categories if c.get("is_active", True)]

    pending_orders = [o for o in orders if o.get('status') == 'pending']
    delivered_orders = [o for o in orders if o.get('status') == 'delivered']
    total_revenue = sum(float(o.get('total_amount', 0)) for o in delivered_orders)

    return render(request, "admin_dashboard.html", {
        "orders": orders,
        "customers": customers,
        "books": books,
        "total_orders": len(orders),
        "total_customers": len(customers),
        "total_books": len(books),
        "total_revenue": total_revenue,
        "pending_orders": pending_orders,
        "total_categories": len(categories),
        "active_categories": active_categories,
    })


@staff_required
def manage_categories(request):
    """Trang quản lý danh mục đơn giản: liệt kê + bật/tắt."""
    message = None
    _ensure_default_categories()
    if request.method == "POST":
        action = request.POST.get("action")
        category_id = request.POST.get("category_id")
        if action == "create":
            name = (request.POST.get("name") or "").strip()
            description = (request.POST.get("description") or "").strip()
            if name:
                try:
                    resp = requests.post(
                        f"{CATALOG_SERVICE_URL}/categories/",
                        json={"name": name, "description": description, "is_active": True},
                        timeout=5,
                    )
                    if resp.status_code in (200, 201):
                        message = "Thêm danh mục thành công."
                    else:
                        message = _friendly_non_json_error(resp)
                except Exception as e:
                    message = f"Lỗi thêm danh mục: {e}"

        elif action == "update" and category_id:
            name = (request.POST.get("name") or "").strip()
            description = (request.POST.get("description") or "").strip()
            is_active = request.POST.get("is_active") == "1"
            try:
                resp = requests.put(
                    f"{CATALOG_SERVICE_URL}/categories/{category_id}/",
                    json={"name": name, "description": description, "is_active": is_active},
                    timeout=5,
                )
                if resp.status_code in (200, 201):
                    message = "Cập nhật danh mục thành công."
                else:
                    message = _friendly_non_json_error(resp)
            except Exception as e:
                message = f"Lỗi cập nhật danh mục: {e}"

        elif action == "delete" and category_id:
            try:
                resp = requests.delete(f"{CATALOG_SERVICE_URL}/categories/{category_id}/", timeout=5)
                if resp.status_code in (200, 204):
                    message = "Đã xoá danh mục."
                else:
                    message = _friendly_non_json_error(resp)
            except Exception as e:
                message = f"Lỗi xoá danh mục: {e}"

        elif action in ("activate", "deactivate") and category_id:
            try:
                # Lấy thông tin cũ
                detail_resp = requests.get(f"{CATALOG_SERVICE_URL}/categories/", timeout=5)
                if detail_resp.status_code == 200:
                    data = detail_resp.json() or []
                    target = next((c for c in data if str(c.get("id")) == str(category_id)), None)
                    if target:
                        payload = {
                            "name": target.get("name"),
                            "description": target.get("description"),
                            "is_active": action == "activate",
                        }
                        requests.put(
                            f"{CATALOG_SERVICE_URL}/categories/{category_id}/",
                            json=payload,
                            timeout=5,
                        )
                        message = "Cập nhật trạng thái danh mục thành công."
            except Exception as e:
                message = f"Lỗi cập nhật danh mục: {e}"

    categories = _load_categories()
    return render(
        request,
        "categories.html",
        {"categories": categories, "message": message},
    )


# Sửa sách
@staff_required
def edit_book(request, book_id):
    if request.method == "POST":
        try:
            response = requests.put(
                f"{BOOK_SERVICE_URL}/books/{book_id}/",
                json={
                    "title": request.POST.get("title"),
                    "author": request.POST.get("author"),
                    "price": float(request.POST.get("price", 0)),
                    "stock": int(request.POST.get("stock", 0)),
                    "description": request.POST.get("description", ""),
                    "category": request.POST.get("category", ""),
                    "publisher": request.POST.get("publisher") or None,
                    "pages": int(request.POST.get("pages") or 0) or None,
                },
                timeout=5
            )
            if response.status_code in [200, 201]:
                return redirect("admin_dashboard")
        except Exception:
            pass

    try:
        book_response = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
        book = book_response.json() if book_response.status_code == 200 else {}
    except Exception:
        book = {}
    categories = _load_categories()
    return render(request, "edit_book.html", {"book": book, "categories": categories})


# Xóa sách
@staff_required
def delete_book(request, book_id):
    if request.method == "POST":
        try:
            requests.delete(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
        except Exception:
            pass
    return redirect("admin_dashboard")


# Quản lý đơn hàng
@staff_required
def manage_orders(request):
    try:
        orders_response = requests.get(f"{ORDER_SERVICE_URL}/orders/", timeout=5)
        orders = orders_response.json() if orders_response.status_code == 200 else []
        if isinstance(orders, dict):
            orders = orders.get('results', [])
    except Exception:
        orders = []
    return render(request, "orders.html", {"orders": orders})


# Cập nhật trạng thái đơn hàng
@staff_required
def update_order_status(request, order_id):
    if request.method == "POST":
        new_status = request.POST.get("status")
        try:
            requests.patch(
                f"{ORDER_SERVICE_URL}/orders/{order_id}/status/",
                json={"status": new_status},
                timeout=5
            )
        except Exception:
            pass
        return redirect("manage_orders")

    try:
        order_response = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}/", timeout=5)
        order = order_response.json() if order_response.status_code == 200 else {}
    except Exception:
        order = {}
    return render(request, "update_order_status.html", {"order": order})


# Quản lý khách hàng
@staff_required
def manage_customers(request):
    try:
        customers_response = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/", timeout=5)
        customers = customers_response.json() if customers_response.status_code == 200 else []
    except Exception:
        customers = []
    return render(request, "customers.html", {"customers": customers})


# Chi tiết khách hàng (admin)
@staff_required
def customer_detail_admin(request, customer_id):
    try:
        customer_response = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/", timeout=5)
        customer = customer_response.json() if customer_response.status_code == 200 else {}
    except Exception:
        customer = {}

    try:
        orders_response = requests.get(f"{ORDER_SERVICE_URL}/orders/customer/{customer_id}/", timeout=5)
        orders = orders_response.json() if orders_response.status_code == 200 else []
    except Exception:
        orders = []

    return render(request, "customer_detail.html", {"customer": customer, "orders": orders})