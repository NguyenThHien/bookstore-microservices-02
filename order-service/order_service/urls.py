from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('orders/', views.OrderListCreate.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', views.OrderDetail.as_view(), name='order-detail'),
    path('orders/<int:order_id>/status/', views.OrderStatusUpdate.as_view(), name='order-status-update'),
    path('orders/customer/<int:customer_id>/', views.CustomerOrders.as_view(), name='customer-orders'),
    path('health/', views.HealthCheck.as_view(), name='health-check'),
]
