"""Promotion model"""
import uuid
from django.db import models


class Promotion(models.Model):
    """Sales promotion/discount"""
    PROMO_TYPE_CHOICES = [
        ('percent', 'Percentage Discount'),
        ('amount', 'Fixed Amount Discount'),
        ('bogo', 'Buy One Get One'),
        ('bundle', 'Bundle Discount'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    corporate_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    promo_type = models.CharField(max_length=20, choices=PROMO_TYPE_CHOICES)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    min_order_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    min_qty = models.IntegerField(default=0)
    
    # Product references (UUID only - data from Inventory service)
    product_id = models.UUIDField(null=True, blank=True, db_index=True)
    free_product_id = models.UUIDField(null=True, blank=True)
    
    date_start = models.DateField()
    date_end = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pos_promotion'
        ordering = ['-date_start']

    def __str__(self):
        return self.name
