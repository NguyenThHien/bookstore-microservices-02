from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('shipments/', views.ShipmentListCreate.as_view(), name='shipment-list-create'),
    path('shipments/<int:pk>/', views.ShipmentDetail.as_view(), name='shipment-detail'),
    path('shipments/<int:shipment_id>/status/', views.ShipmentUpdateStatus.as_view(), name='shipment-status-update'),
    path('shipments/<int:shipment_id>/tracking/', views.ShipmentTrackingHistory.as_view(), name='shipment-tracking'),
    path('shipments/lookup/', views.TrackingNumberLookup.as_view(), name='tracking-lookup'),
    path('shipments/statistics/', views.ShipmentStatistics.as_view(), name='shipment-statistics'),
    path('orders/<int:order_id>/shipment/', views.OrderShipment.as_view(), name='order-shipment'),
    path('health/', views.HealthCheck.as_view(), name='health-check'),
]
