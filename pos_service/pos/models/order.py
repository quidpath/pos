"""POS Order models - transactions"""
import uuid
from decimal import Decimal
from django.db import models
from .session import POSSession
from .loyalty import LoyaltyCard


class POSOrder(models.Model):
    """POS order/sale transaction"""
    STATE_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    corporate_id = models.UUIDField(db_index=True)
    session = models.ForeignKey(POSSession, on_delete=models.CASCADE, related_name='orders', 
                                null=True, blank=True, help_text="Optional: POS session (for in-store sales)")
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    customer_id = models.UUIDField(null=True, blank=True, db_index=True)
    customer_name = models.CharField(max_length=255, blank=True)
    loyalty_card = models.ForeignKey(LoyaltyCard, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='draft')
    
    # Payment account for accounting integration
    payment_account_id = models.UUIDField(null=True, blank=True, db_index=True, 
                                         help_text="Accounting account where payment was received")
    
    # Amounts
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Loyalty
    points_earned = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)
    
    # Invoice integration
    invoice_id = models.UUIDField(null=True, blank=True, db_index=True)
    is_invoiced = models.BooleanField(default=False)
    invoiced_at = models.DateTimeField(null=True, blank=True)
    invoiced_by = models.UUIDField(null=True, blank=True)
    
    # Accounting sync status
    accounting_synced = models.BooleanField(default=False, 
                                           help_text="Whether order has been synced to accounting")
    accounting_sync_error = models.TextField(blank=True, 
                                            help_text="Error message if accounting sync failed")
    
    notes = models.TextField(blank=True)
    cashier_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'pos_order'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['corporate_id', 'created_at']),
            models.Index(fields=['session', 'state']),
            models.Index(fields=['accounting_synced', 'state']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def calculate_totals(self):
        """Calculate and update order totals based on order lines"""
        lines = self.lines.all()
        
        # Calculate subtotal from all lines
        subtotal = sum(line.subtotal for line in lines)
        
        # For now, we'll use simple calculations
        # This can be enhanced later with proper tax calculations
        self.subtotal = subtotal
        self.total_amount = subtotal - self.discount_amount + self.tax_amount
        
        # Update line subtotals
        for line in lines:
            line.discount_amount = (line.unit_price * line.quantity * line.discount_percent) / 100
            line.subtotal = (line.unit_price * line.quantity) - line.discount_amount
            line.save()
        
        self.save()


class POSOrderLine(models.Model):
    """POS order line item - references product in Inventory service"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name='lines')
    
    # Product reference (UUID only - data comes from Inventory service)
    product_id = models.UUIDField(db_index=True)
    variant_id = models.UUIDField(null=True, blank=True)
    
    # Cached product info (for display/receipt - not authoritative)
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True)
    
    # Transaction details
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Traceability
    lot_id = models.UUIDField(null=True, blank=True)
    serial_number = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'pos_order_line'
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class POSPayment(models.Model):
    """Payment for POS order"""
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('loyalty', 'Loyalty Points'),
        ('other', 'Other'),
    ]
    
    STATE_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name='payments')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='pending')
    reference = models.CharField(max_length=255, blank=True)
    mpesa_checkout_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pos_payment'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.method} - {self.amount}"
