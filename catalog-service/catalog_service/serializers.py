from rest_framework import serializers
from .models import Category, Subcategory

class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'is_active']

class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(source='subcategory_set', many=True, read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'subcategories']
