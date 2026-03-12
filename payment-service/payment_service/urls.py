from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('payments/', views.PaymentListCreate.as_view(), name='payment-list-create'),
    path('payments/<int:pk>/', views.PaymentDetail.as_view(), name='payment-detail'),
    path('payments/<int:payment_id>/process/', views.PaymentProcess.as_view(), name='payment-process'),
    path('payments/<int:payment_id>/refund/', views.PaymentRefund.as_view(), name='payment-refund'),
    path('payments/statistics/', views.PaymentStatistics.as_view(), name='payment-statistics'),
    path('orders/<int:order_id>/payment/', views.OrderPayment.as_view(), name='order-payment'),
    path('health/', views.HealthCheck.as_view(), name='health-check'),
]
