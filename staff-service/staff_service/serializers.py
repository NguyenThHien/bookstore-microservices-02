from rest_framework import serializers
from .models import Staff, StaffActivity, Shift

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['id', 'name', 'email', 'role', 'phone', 'permissions', 'is_active', 'last_login', 'created_at', 'updated_at']

class StaffActivitySerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    
    class Meta:
        model = StaffActivity
        fields = ['id', 'staff', 'staff_name', 'action', 'resource_type', 'resource_id', 'description', 'timestamp']

class ShiftSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    
    class Meta:
        model = Shift
        fields = ['id', 'staff', 'staff_name', 'start_time', 'end_time', 'status', 'notes', 'created_at', 'updated_at']

