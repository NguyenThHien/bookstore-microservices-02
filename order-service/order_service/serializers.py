from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'book_id', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id',
            'customer_id',
            'total_amount',
            'discount_amount',
            'status',
            'shipping_address',
            'shipping_city',
            'shipping_zip',
            'shipping_country',
            'billing_address',
            'billing_city',
            'billing_zip',
            'billing_country',
            'notes',
            'created_at',
            'updated_at',
            'items',
        ]
