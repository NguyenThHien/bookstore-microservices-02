from rest_framework import serializers
from .models import Rating

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'book_id', 'customer_id', 'rating', 'comment', 'is_verified', 'helpful_count', 'created_at']
