from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
import requests

BOOK_SERVICE_URL = "http://book-service:8000"

class CartCreate(APIView):
    def post(self, request):
        customer_id = request.data.get('customer_id')
        
        # Check if cart already exists
        try:
            cart = Cart.objects.get(customer_id=customer_id)
            serializer = CartSerializer(cart)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            serializer = CartSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddCartItem(APIView):
    def post(self, request):
        cart_id = request.data.get('cart')
        book_id = request.data.get('book_id')
        quantity = request.data.get('quantity', 1)
        
        # Verify book exists and get its price
        try:
            book_response = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
            if book_response.status_code != 200:
                return Response(
                    {"error": "Book not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            book = book_response.json()
            price = float(book.get('price', 0))
        except Exception as e:
            return Response(
                {"error": f"Error verifying book: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            cart = Cart.objects.get(id=cart_id)
            
            # Check if item already in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                book_id=book_id,
                defaults={'quantity': quantity, 'price': price}
            )
            
            if not created:
                # Update quantity if item already exists
                cart_item.quantity += quantity
                cart_item.save()
            
            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Cart not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class UpdateCartItem(APIView):
    def put(self, request, item_id):
        """Update cart item quantity"""
        try:
            cart_item = CartItem.objects.get(id=item_id)
            quantity = request.data.get('quantity')
            
            if quantity is not None:
                if quantity <= 0:
                    # Delete if quantity is 0 or negative
                    cart_item.delete()
                    return Response(
                        {"message": "Item removed from cart"},
                        status=status.HTTP_204_NO_CONTENT
                    )
                else:
                    cart_item.quantity = quantity
                    cart_item.save()
            
            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class DeleteCartItem(APIView):
    def delete(self, request, item_id):
        """Delete cart item"""
        try:
            cart_item = CartItem.objects.get(id=item_id)
            cart_item.delete()
            return Response(
                {"message": "Item removed from cart"},
                status=status.HTTP_204_NO_CONTENT
            )
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class ViewCart(APIView):
    def get(self, request, customer_id):
        """Get all items in customer's cart"""
        try:
            cart = Cart.objects.get(customer_id=customer_id)
            items = CartItem.objects.filter(cart=cart)
            serializer = CartItemSerializer(items, many=True)
            return Response(serializer.data)
        except Cart.DoesNotExist:
            return Response({"items": []})

class GetCart(APIView):
    def get(self, request, customer_id):
        """Get cart object with summary"""
        try:
            cart = Cart.objects.get(customer_id=customer_id)
            serializer = CartSerializer(cart)
            data = serializer.data
            # Add computed fields
            items = CartItem.objects.filter(cart=cart)
            data['item_count'] = sum(item.quantity for item in items)
            data['total_price'] = sum(item.price * item.quantity for item in items)
            return Response(data)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Cart not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class ClearCart(APIView):
    def delete(self, request, customer_id):
        """Clear all items from cart"""
        try:
            cart = Cart.objects.get(customer_id=customer_id)
            cart.clear()
            return Response(
                {"message": "Cart cleared successfully"},
                status=status.HTTP_200_OK
            )
        except Cart.DoesNotExist:
            return Response(
                {"error": "Cart not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class HealthCheck(APIView):
    def get(self, request):
        return Response({"status": "Cart service is running"})
