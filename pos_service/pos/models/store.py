"""Store model - POS location configuration"""
import uuid
from django.db import models


class Store(models.Model):
    """Physical store location"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    corporate_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    currency = models.CharField(max_length=3, default='KES')
    receipt_header = models.TextField(blank=True)
    receipt_footer = models.TextField(blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pos_store'
        ordering = ['name']

    def __str__(self):
        return self.name
