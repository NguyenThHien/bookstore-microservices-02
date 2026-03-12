from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('recommendations/', views.RecommendationList.as_view(), name='recommendation-list'),
    path('recommendations/<int:pk>/', views.RecommendationDetail.as_view(), name='recommendation-detail'),
    path('customers/<int:customer_id>/recommendations/', views.CustomerRecommendations.as_view(), name='customer-recommendations'),
    path('customers/<int:customer_id>/generate/', views.GenerateRecommendations.as_view(), name='generate-recommendations'),
    path('customers/<int:customer_id>/preferences/', views.CustomerPreferenceUpdate.as_view(), name='customer-preferences'),
    path('view-history/', views.ViewHistoryCreate.as_view(), name='view-history'),
    path('purchases/', views.RecordPurchase.as_view(), name='record-purchase'),
    path('health/', views.HealthCheck.as_view(), name='health-check'),
]
