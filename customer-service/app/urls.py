from django.urls import path
from .views import CustomerListCreate, CustomerDetail, CustomerVerifyPassword, HealthCheck

urlpatterns = [
    path('', HealthCheck.as_view()),
    path('customers/', CustomerListCreate.as_view()),
    path('customers/verify-password/', CustomerVerifyPassword.as_view()),
    path('customers/<int:pk>/', CustomerDetail.as_view()),
]