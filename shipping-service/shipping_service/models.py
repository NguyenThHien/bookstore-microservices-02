from django.db import models
from django.utils import timezone
import uuid

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    CARRIER_CHOICES = [
        ('viettel', 'Viettel Post'),
        ('vietnampost', 'Vietnam Post'),
        ('ghn', 'Giao Hang Nhanh (GHN)'),
        ('grab', 'Grab Express'),
        ('standard', 'Standard Shipping'),
    ]
    
    order_id = models.IntegerField(db_index=True)
    customer_id = models.IntegerField(db_index=True, null=True, blank=True)
    tracking_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Address info
    address = models.TextField()
    city = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    recipient_name = models.CharField(max_length=255, null=True, blank=True)
    recipient_phone = models.CharField(max_length=20, null=True, blank=True)
    
    # Carrier info
    carrier = models.CharField(max_length=50, choices=CARRIER_CHOICES, default='standard')
    carrier_reference = models.CharField(max_length=100, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    
    # Tracking history
    last_location = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"Shipment #{self.id} - Order {self.order_id}"
    
    def generate_tracking_number(self):
        """Generate unique tracking number"""
        if not self.tracking_number:
            self.tracking_number = f"VN{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"


class TrackingUpdate(models.Model):
    """Track history of shipment status changes"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_updates')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    location = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Update: {self.shipment.id} - {self.status}"

