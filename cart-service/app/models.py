from django.db import models
from django.utils import timezone

class Cart(models.Model):
    customer_id = models.IntegerField(unique=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for Customer {self.customer_id}"
    
    def get_total_price(self):
        """Calculate total price of all items in cart"""
        return sum(item.get_subtotal() for item in self.items.all())
    
    def get_item_count(self):
        """Get total quantity of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book_id = models.IntegerField(db_index=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Price at time of adding
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'book_id']
    
    def __str__(self):
        return f"Cart {self.cart.id} - Book {self.book_id}"
    
    def get_subtotal(self):
        """Calculate subtotal for this item"""
        return self.price * self.quantity

