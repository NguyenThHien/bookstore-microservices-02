from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
import requests
from .models import Order, OrderItem
from .serializers import OrderSerializer

BOOK_SERVICE_URL = "http://book-service:8000"
PAY_SERVICE_URL = "http://pay-service:8000"
SHIP_SERVICE_URL = "http://ship-service:8000"

class OrderListCreate(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        customer_id = request.data.get('customer_id')
        total_amount = request.data.get('total_amount')
        items = request.data.get('items', [])
        payment_method = request.data.get('payment_method', 'card')
        shipping_method = request.data.get('shipping_method', 'standard')
        shipping_address = request.data.get('shipping_address', '')
        shipping_city = request.data.get('shipping_city', '')
        shipping_zip = request.data.get('shipping_zip', '')
        shipping_country = request.data.get('shipping_country', '')
        billing_address = request.data.get('billing_address', shipping_address)
        billing_city = request.data.get('billing_city', shipping_city)
        billing_zip = request.data.get('billing_zip', shipping_zip)
        billing_country = request.data.get('billing_country', shipping_country)
        
        # Validate stock availability before creating order
        for item in items:
            book_id = item.get('book_id')
            quantity = item.get('quantity')
            
            # Check book stock from book service
            try:
                book_response = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
                if book_response.status_code == 200:
                    book = book_response.json()
                    if book.get('stock', 0) < quantity:
                        return Response(
                            {"error": f"Insufficient stock for book {book_id}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    return Response(
                        {"error": f"Book {book_id} not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            except Exception as e:
                return Response(
                    {"error": f"Error checking book availability: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Create order
        order = Order.objects.create(
            customer_id=customer_id,
            total_amount=total_amount,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_zip=shipping_zip,
            shipping_country=shipping_country,
            billing_address=billing_address,
            billing_city=billing_city,
            billing_zip=billing_zip,
            billing_country=billing_country
        )
        
        # Create order items and decrement book stock
        for item in items:
            book_id = item.get('book_id')
            quantity = item.get('quantity')
            price = item.get('price')
            
            OrderItem.objects.create(
                order=order,
                book_id=book_id,
                quantity=quantity,
                price=price
            )
            
            # Decrement stock in book service
            try:
                book_response = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
                if book_response.status_code == 200:
                    book_data = book_response.json()
                    new_stock = book_data.get('stock', 0) - quantity
                    requests.put(
                        f"{BOOK_SERVICE_URL}/books/{book_id}/",
                        json={'stock': new_stock},
                        timeout=5
                    )
            except:
                pass  # Stock update is non-critical

        # Trigger payment + shipping (best-effort, non-blocking to order creation)
        try:
            requests.post(
                f"{PAY_SERVICE_URL}/payments/",
                json={
                    "order_id": order.id,
                    "customer_id": customer_id,
                    "amount": total_amount,
                    "payment_method": payment_method,
                },
                timeout=5
            )
        except Exception:
            pass

        try:
            requests.post(
                f"{SHIP_SERVICE_URL}/shipments/",
                json={
                    "order_id": order.id,
                    "customer_id": customer_id,
                    "address": shipping_address or billing_address or "",
                    "carrier": shipping_method,
                },
                timeout=5
            )
        except Exception:
            pass

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    
    def update(self, request, *args, **kwargs):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status and new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)


class OrderStatusUpdate(APIView):
    """Update order status"""
    def put(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            new_status = request.data.get('status')
            
            if new_status and order.update_status(new_status):
                serializer = OrderSerializer(order)
                return Response(serializer.data)
            else:
                return Response(
                    {"error": "Invalid status"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class CustomerOrders(generics.ListAPIView):
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        customer_id = self.kwargs['customer_id']
        return Order.objects.filter(customer_id=customer_id).order_by('-created_at')


class HealthCheck(APIView):
    def get(self, request):
        return Response({"status": "Order service healthy"}, status=status.HTTP_200_OK)
