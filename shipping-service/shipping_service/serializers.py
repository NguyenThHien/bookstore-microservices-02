from rest_framework import serializers
from .models import Shipment, TrackingUpdate


class TrackingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingUpdate
        fields = ['id', 'status', 'location', 'description', 'created_at']


class ShipmentSerializer(serializers.ModelSerializer):
    tracking_updates = TrackingUpdateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Shipment
        fields = [
            'id', 'order_id', 'customer_id', 'tracking_number', 'status',
            'address', 'city', 'zip_code', 'country',
            'recipient_name', 'recipient_phone',
            'carrier', 'carrier_reference',
            'created_at', 'updated_at', 'shipped_at', 'delivered_at',
            'estimated_delivery_date', 'last_location', 'tracking_updates'
        ]
