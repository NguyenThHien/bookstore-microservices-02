from rest_framework import serializers
from .models import Recommendation, ViewHistory, PurchaseHistory, CustomerPreference

class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = ['id', 'customer_id', 'recommended_book_ids', 'scores', 'algorithm', 'confidence', 'reason', 'generated_at', 'updated_at']

class ViewHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewHistory
        fields = ['id', 'customer_id', 'book_id', 'category', 'duration', 'viewed_at']

class PurchaseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseHistory
        fields = ['id', 'customer_id', 'book_id', 'category', 'price', 'rating', 'purchased_at']

class CustomerPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerPreference
        fields = ['id', 'customer_id', 'preferred_categories', 'preferred_authors', 'price_preference', 'rating_threshold', 'updated_at']

