from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def set_password(self, raw_password):
        """Hash the password using Django's password hasher"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check if the raw password matches the stored hash"""
        return check_password(raw_password, self.password)
    
    def save(self, *args, **kwargs):
        # If password looks like plaintext (not hashed), hash it
        if self.password and not self.password.startswith('pbkdf2_sha256$') and not self.password.startswith('argon2$') and not self.password.startswith('bcrypt$'):
            self.set_password(self.password)
        super().save(*args, **kwargs)
