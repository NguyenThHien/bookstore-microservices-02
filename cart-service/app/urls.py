from django.urls import path
from .views import (CartCreate, AddCartItem, UpdateCartItem, DeleteCartItem, 
                    ViewCart, GetCart, ClearCart, HealthCheck)

urlpatterns = [
    path('', HealthCheck.as_view()),
    path('carts/', CartCreate.as_view()),
    path('carts/<int:customer_id>/', ViewCart.as_view()),
    path('carts/get/<int:customer_id>/', GetCart.as_view()),
    path('carts/<int:customer_id>/clear/', ClearCart.as_view()),
    path('cart-items/', AddCartItem.as_view()),
    path('cart-items/<int:item_id>/', UpdateCartItem.as_view()),
    path('cart-items/<int:item_id>/delete/', DeleteCartItem.as_view()),
]