from django.db import models
from django.utils import timezone

class Recommendation(models.Model):
    ALGORITHM_CHOICES = [
        ('collaborative_filtering', 'Collaborative Filtering'),
        ('content_based', 'Content-Based'),
        ('hybrid', 'Hybrid'),
        ('trending', 'Trending'),
        ('popular', 'Popular Books'),
    ]
    
    customer_id = models.IntegerField(unique=True, db_index=True)
    recommended_book_ids = models.JSONField(default=list)
    scores = models.JSONField(default=dict)
    algorithm = models.CharField(choices=ALGORITHM_CHOICES, default='hybrid', max_length=100)
    confidence = models.FloatField(default=0.0)
    reason = models.CharField(max_length=255, null=True, blank=True)
    generated_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Recommendations for Customer {self.customer_id}"

class ViewHistory(models.Model):
    customer_id = models.IntegerField(db_index=True)
    book_id = models.IntegerField(db_index=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    duration = models.IntegerField(default=0)  # Time spent viewing in seconds
    viewed_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        indexes = [models.Index(fields=['customer_id', '-viewed_at'])]
        unique_together = ['customer_id', 'book_id', 'viewed_at']
    
    def __str__(self):
        return f"View: Customer {self.customer_id} - Book {self.book_id}"

class PurchaseHistory(models.Model):
    """Track customer purchase history for recommendations"""
    customer_id = models.IntegerField(db_index=True)
    book_id = models.IntegerField(db_index=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rating = models.IntegerField(default=0)  # 1-5 stars if customer rated
    purchased_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['customer_id', 'book_id']
        ordering = ['-purchased_at']
    
    def __str__(self):
        return f"Purchase: Customer {self.customer_id} - Book {self.book_id}"

class CustomerPreference(models.Model):
    """Store customer preferences for recommendations"""
    customer_id = models.IntegerField(unique=True, db_index=True)
    preferred_categories = models.JSONField(default=list)  # List of category names
    preferred_authors = models.JSONField(default=list)  # List of author names
    price_preference = models.CharField(
        max_length=20,
        choices=[('budget', 'Budget'), ('mid', 'Mid-range'), ('premium', 'Premium'), ('any', 'Any')],
        default='any'
    )
    rating_threshold = models.FloatField(default=0.0)  # Only recommend books with rating >= this
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for Customer {self.customer_id}"

