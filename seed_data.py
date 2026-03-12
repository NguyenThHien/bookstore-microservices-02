"""
Seed dữ liệu demo cho Assignment 05:
- Admin (staff-service) + tài khoản đăng nhập (customer-service)
- Users (customer-service)
- Categories (catalog-service)
- Books (book-service)

Chạy sau khi docker compose up:
  python seed_data.py
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from typing import Any


SERVICES = {
    "customer": "http://localhost:8001",
    "staff": "http://localhost:8010",
    "catalog": "http://localhost:8007",
    "book": "http://localhost:8002",
}


def _print(msg: str) -> None:
    # Windows console sometimes uses cp1252 → avoid crashing on unicode icons.
    try:
        print(msg)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "cp1252"
        safe = msg.encode(enc, errors="replace").decode(enc, errors="replace")
        print(safe)


def _request(method: str, url: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        data = body
        headers["Content-Type"] = "application/json; charset=utf-8"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.getcode()
            raw = resp.read()
            text = raw.decode("utf-8", errors="replace")
            try:
                return status, json.loads(text)
            except Exception:
                return status, text
    except urllib.error.HTTPError as e:
        raw = e.read()
        text = raw.decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(text)
        except Exception:
            return e.code, text
    except Exception as e:
        return 0, str(e)


def _post(url: str, payload: dict[str, Any]) -> tuple[int, Any]:
    return _request("POST", url, payload)


def _get(url: str, params: dict[str, Any] | None = None) -> tuple[int, Any]:
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        url = f"{url}?{query}"
    return _request("GET", url, None)


def _put(url: str, payload: dict[str, Any]) -> tuple[int, Any]:
    return _request("PUT", url, payload)


def ensure_customer(name: str, email: str, password: str) -> None:
    code, data = _post(f"{SERVICES['customer']}/customers/", {"name": name, "email": email, "password": password})
    if code in (200, 201):
        _print(f"[OK] customer created: {email}")
        return
    # if already exists (unique email) customer-service returns 400
    if code == 400:
        _print(f"[SKIP] customer exists: {email}")
        return
    _print(f"[ERR] customer error {code}: {data}")


def ensure_staff(name: str, email: str, role: str, permissions: list[str] | None = None) -> None:
    # staff-service list supports ?email=
    code, data = _get(f"{SERVICES['staff']}/staff/", params={"email": email})
    if code == 200 and isinstance(data, list) and data:
        staff_id = data[0].get("id")
        _print(f"[SKIP] staff exists: {email} (id={staff_id})")
        return

    payload = {
        "name": name,
        "email": email,
        "role": role,
        "permissions": permissions or [],
        "is_active": True,
    }
    code, data = _post(f"{SERVICES['staff']}/staff/", payload)
    if code in (200, 201):
        _print(f"[OK] staff created: {email} (role={role})")
        return
    if code == 400:
        _print(f"[SKIP] staff maybe exists: {email}")
        return
    _print(f"[ERR] staff error {code}: {data}")


def ensure_categories(categories: list[dict[str, Any]]) -> None:
    code, existing = _get(f"{SERVICES['catalog']}/categories/")
    if code != 200 or not isinstance(existing, list):
        _print(f"[ERR] cannot load categories: {code} {existing}")
        return

    names = {str(c.get("name", "")).strip().lower() for c in existing}
    for c in categories:
        if c["name"].strip().lower() in names:
            continue
        code, data = _post(f"{SERVICES['catalog']}/categories/", c)
        if code in (200, 201):
            _print(f"[OK] category created: {c['name']}")
        else:
            _print(f"[ERR] category error {code}: {data}")


def ensure_books(books: list[dict[str, Any]]) -> None:
    # get current books for de-dup by title+author
    code, data = _get(f"{SERVICES['book']}/books/", params={"limit": 200})
    existing = []
    if code == 200 and isinstance(data, dict):
        existing = data.get("results", []) or []
    existing_keys = {(b.get("title"), b.get("author")) for b in existing if isinstance(b, dict)}

    for b in books:
        key = (b.get("title"), b.get("author"))
        if key in existing_keys:
            _print(f"[SKIP] book exists: {b.get('title')}")
            continue
        code, resp = _post(f"{SERVICES['book']}/books/", b)
        if code in (200, 201):
            _print(f"[OK] book created: {b.get('title')}")
        else:
            _print(f"[ERR] book error {code}: {resp}")


def main() -> int:
    # Categories like your screenshot
    ensure_categories(
        [
            {"name": "Lập trình", "description": "Sách lập trình, công nghệ", "is_active": True},
            {"name": "Kỹ năng sống", "description": "Kỹ năng, phát triển bản thân", "is_active": True},
            {"name": "Tiểu thuyết", "description": "Văn học, tiểu thuyết", "is_active": True},
            {"name": "Tài chính", "description": "Tài chính, đầu tư", "is_active": True},
            {"name": "Tâm lý học", "description": "Tâm lý, hành vi", "is_active": True},
            {"name": "Lịch sử", "description": "Lịch sử, văn hóa", "is_active": True},
        ]
    )

    # Accounts
    # Customer account used for login via gateway
    ensure_customer("Admin Login", "admin@example.com", "Admin123!")
    ensure_staff(
        "Admin Staff",
        "admin@example.com",
        role="admin",
        permissions=[
            "view_books",
            "edit_books",
            "delete_books",
            "view_orders",
            "edit_orders",
            "view_customers",
            "edit_customers",
            "view_reports",
            "export_data",
        ],
    )

    ensure_customer("John Doe", "john@example.com", "password123")
    ensure_customer("Jane Doe", "jane@example.com", "password123")

    # Books
    ensure_books(
        [
            {
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "price": 299900,
                "stock": 15,
                "description": "Best practices for writing clean code.",
                "category": "Lập trình",
                "publisher": "Prentice Hall",
                "pages": 464,
            },
            {
                "title": "The Pragmatic Programmer",
                "author": "David Thomas",
                "price": 319900,
                "stock": 12,
                "description": "A classic guide for modern software development.",
                "category": "Lập trình",
                "publisher": "Addison-Wesley",
                "pages": 352,
            },
            {
                "title": "Atomic Habits",
                "author": "James Clear",
                "price": 199900,
                "stock": 25,
                "description": "Small habits, big results.",
                "category": "Kỹ năng sống",
                "publisher": "Avery",
                "pages": 320,
            },
            {
                "title": "Tâm lý học hành vi",
                "author": "Nhiều tác giả",
                "price": 189900,
                "stock": 20,
                "description": "Những nguyên lý tâm lý học ứng dụng trong đời sống.",
                "category": "Tâm lý học",
                "pages": 280,
            },
            {
                "title": "Nhà giả kim",
                "author": "Paulo Coelho",
                "price": 149900,
                "stock": 18,
                "description": "Tiểu thuyết nổi tiếng về hành trình theo đuổi ước mơ.",
                "category": "Tiểu thuyết",
                "pages": 208,
            },
        ]
    )

    _print("\n=== Accounts ===")
    _print("Admin login (gateway): admin@example.com / Admin123!")
    _print("User login: john@example.com / password123")
    _print("User login: jane@example.com / password123")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

