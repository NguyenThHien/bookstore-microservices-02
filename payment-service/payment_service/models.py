from django.db import models
from django.utils import timezone
import uuid

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]
    
    order_id = models.IntegerField(db_index=True)
    customer_id = models.IntegerField(db_index=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='credit_card')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Transaction info
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    reference_number = models.CharField(max_length=100, default=uuid.uuid4)
    
    # Card info (encrypted in real system)
    card_last_four = models.CharField(max_length=4, null=True, blank=True)
    card_brand = models.CharField(max_length=50, null=True, blank=True)
    
    # Refund info
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_transaction_id = models.CharField(max_length=100, null=True, blank=True)
    refund_reason = models.TextField(null=True, blank=True)
    refund_status = models.CharField(max_length=20, default='none')  # none, pending, completed
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payment #{self.id} - Order {self.order_id}"
    
    def process_payment(self):
        """Process the payment (simulate payment gateway integration)"""
        self.status = 'processing'
        self.save()
        
        # In real system, call payment gateway (Stripe, PayPal, etc.)
        # For now, we simulate success
        self.status = 'completed'
        self.transaction_id = str(uuid.uuid4())
        self.completed_at = timezone.now()
        self.save()
        return True
    
    def refund(self, refund_amount=None, reason=''):
        """Refund the payment"""
        if self.status != 'completed':
            return False
        
        if refund_amount is None:
            refund_amount = self.amount
        
        if refund_amount > (self.amount - self.refund_amount):
            return False  # Cannot refund more than paid
        
        self.refund_amount += refund_amount
        self.refund_reason = reason
        self.refund_status = 'completed'
        self.refund_transaction_id = str(uuid.uuid4())
        self.save()
        return True

