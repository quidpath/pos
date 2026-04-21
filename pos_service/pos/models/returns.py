"""Return/refund models"""
import uuid
from django.db import models
from .order import POSOrder, POSOrderLine


class ReturnOrder(models.Model):
    """Product return/refund"""
    STATE_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    REFUND_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mpesa', 'M-Pesa'),
        ('store_credit', 'Store Credit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name='returns')
    return_number = models.CharField(max_length=50, unique=True, db_index=True)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='draft')
    refund_method = models.CharField(max_length=20, choices=REFUND_METHOD_CHOICES)
    total_refund = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pos_return_order'
        ordering = ['-created_at']

    def __str__(self):
        return f"Return {self.return_number}"


class ReturnOrderLine(models.Model):
    """Return order line item"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    return_order = models.ForeignKey(ReturnOrder, on_delete=models.CASCADE, related_name='lines')
    original_line = models.ForeignKey(POSOrderLine, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    refund_amount = models.DecimalField(max_digits=15, decimal_places=2)
    reason = models.TextField(blank=True)

    class Meta:
        db_table = 'pos_return_order_line'
        ordering = ['return_order', 'id']

    def __str__(self):
        return f"Return line for {self.original_line.product_name}"
