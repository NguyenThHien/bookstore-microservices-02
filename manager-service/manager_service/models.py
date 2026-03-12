from django.db import models

class Report(models.Model):
    TYPE_CHOICES = [('sales', 'Sales'), ('inventory', 'Inventory'), ('customer', 'Customer')]
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} ({self.report_type})"
