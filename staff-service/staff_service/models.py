from django.db import models
from django.utils import timezone

class Staff(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('operator', 'Operator'),
        ('accountant', 'Accountant'),
        ('inventory', 'Inventory Manager')
    ]
    
    PERMISSION_CHOICES = [
        ('view_books', 'View Books'),
        ('edit_books', 'Edit Books'),
        ('delete_books', 'Delete Books'),
        ('view_orders', 'View Orders'),
        ('edit_orders', 'Edit Orders'),
        ('view_payments', 'View Payments'),
        ('edit_payments', 'Edit Payments'),
        ('view_shipments', 'View Shipments'),
        ('edit_shipments', 'Edit Shipments'),
        ('view_customers', 'View Customers'),
        ('edit_customers', 'Edit Customers'),
        ('view_staff', 'View Staff'),
        ('edit_staff', 'Edit Staff'),
        ('view_reports', 'View Reports'),
        ('export_data', 'Export Data'),
    ]
    
    # Basic info
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operator')
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Permissions
    permissions = models.JSONField(default=list)  # List of permission strings
    
    # Status
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.role})"
    
    def has_permission(self, permission):
        """Check if staff has a specific permission"""
        return permission in self.permissions or self.role == 'admin'


class StaffActivity(models.Model):
    """Log staff activities for audit trail"""
    ACTION_CHOICES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]
    
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name='activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=100)  # 'Book', 'Order', 'Customer', etc.
    resource_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.staff.name} - {self.action} {self.resource_type} at {self.timestamp}"


class Shift(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='shifts')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.staff.name} - {self.start_time}"

