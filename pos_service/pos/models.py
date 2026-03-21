from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from pos_service.core.base_models import BaseModel


class Store(BaseModel):
    corporate_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    currency = models.CharField(max_length=3, default="KES")
    receipt_header = models.TextField(blank=True)
    receipt_footer = models.TextField(blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("16.0"), help_text="VAT %")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class POSTerminal(BaseModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="terminals")
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.store.name} — {self.name}"


class POSSession(BaseModel):
    """Cashier shift / session."""
    STATES = [("open", "Open"), ("closing_control", "Closing Control"), ("closed", "Closed")]

    terminal = models.ForeignKey(POSTerminal, on_delete=models.PROTECT, related_name="sessions")
    cashier_id = models.UUIDField()
    state = models.CharField(max_length=20, choices=STATES, default="open")
    opening_cash = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    closing_cash = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    expected_cash = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    cash_difference = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def close(self, closing_cash: Decimal):
        cash_orders = self.orders.filter(state="paid").aggregate(
            total=models.Sum("amount_paid")
        )["total"] or Decimal("0")
        self.expected_cash = self.opening_cash + cash_orders
        self.closing_cash = closing_cash
        self.cash_difference = closing_cash - self.expected_cash
        self.state = "closed"
        self.closed_at = timezone.now()
        self.save()


class Promotion(BaseModel):
    PROMO_TYPES = [
        ("percent_discount", "Percentage Discount"),
        ("fixed_discount", "Fixed Amount Discount"),
        ("bogo", "Buy One Get One"),
        ("bundle", "Bundle Deal"),
        ("free_item", "Free Item"),
    ]

    corporate_id = models.UUIDField(db_index=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True, related_name="promotions")
    name = models.CharField(max_length=200)
    promo_type = models.CharField(max_length=30, choices=PROMO_TYPES)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    min_order_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    min_qty = models.PositiveIntegerField(default=1)
    product_id = models.UUIDField(null=True, blank=True, help_text="Specific product for BOGO/bundle")
    free_product_id = models.UUIDField(null=True, blank=True)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class LoyaltyProgram(BaseModel):
    corporate_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=200)
    points_per_currency = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal("1.0"))
    redemption_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal("0.01"), help_text="KES value per point")
    min_points_redemption = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class LoyaltyCard(BaseModel):
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name="cards")
    customer_id = models.UUIDField(db_index=True)
    card_number = models.CharField(max_length=50, unique=True, db_index=True)
    points_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total_earned = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total_redeemed = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Card {self.card_number} — {self.points_balance} pts"


class POSOrder(BaseModel):
    STATES = [
        ("draft", "Draft"),
        ("paid", "Paid"),
        ("invoiced", "Invoiced"),
        ("cancelled", "Cancelled"),
        ("returned", "Returned"),
    ]

    corporate_id = models.UUIDField(db_index=True)
    session = models.ForeignKey(POSSession, on_delete=models.PROTECT, related_name="orders")
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    customer_id = models.UUIDField(null=True, blank=True)
    customer_name = models.CharField(max_length=200, blank=True)
    loyalty_card = models.ForeignKey(LoyaltyCard, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.CharField(max_length=20, choices=STATES, default="draft")
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    change_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    points_earned = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    points_redeemed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    notes = models.TextField(blank=True)
    cashier_id = models.UUIDField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number}"

    def calculate_totals(self):
        lines = self.lines.all()
        self.subtotal = sum(l.subtotal for l in lines)
        self.discount_amount = sum(l.discount_amount for l in lines)
        taxable = self.subtotal - self.discount_amount
        store = self.session.terminal.store
        self.tax_amount = taxable * store.tax_rate / Decimal("100")
        self.total_amount = taxable + self.tax_amount
        self.save()


class POSOrderLine(BaseModel):
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name="lines")
    product_id = models.UUIDField()
    variant_id = models.UUIDField(null=True, blank=True)
    product_name = models.CharField(max_length=300)
    sku = models.CharField(max_length=150, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))])
    unit_price = models.DecimalField(max_digits=14, decimal_places=4)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    lot_id = models.UUIDField(null=True, blank=True)
    serial_number = models.CharField(max_length=200, blank=True)
    notes = models.CharField(max_length=300, blank=True)

    def save(self, *args, **kwargs):
        line_total = self.quantity * self.unit_price
        self.discount_amount = line_total * self.discount_percent / Decimal("100")
        self.subtotal = line_total - self.discount_amount
        super().save(*args, **kwargs)


class POSPayment(BaseModel):
    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("card", "Credit/Debit Card"),
        ("mpesa", "M-Pesa"),
        ("bank_transfer", "Bank Transfer"),
        ("loyalty_points", "Loyalty Points"),
        ("credit", "Customer Credit"),
        ("cheque", "Cheque"),
    ]
    STATES = [("pending", "Pending"), ("confirmed", "Confirmed"), ("failed", "Failed"), ("reversed", "Reversed")]

    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name="payments")
    method = models.CharField(max_length=30, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    state = models.CharField(max_length=20, choices=STATES, default="pending")
    reference = models.CharField(max_length=200, blank=True, help_text="M-Pesa code, card ref, etc.")
    mpesa_checkout_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.get_method_display()} {self.amount}"


class ReturnOrder(BaseModel):
    STATES = [("draft", "Draft"), ("validated", "Validated"), ("refunded", "Refunded")]

    corporate_id = models.UUIDField(db_index=True)
    original_order = models.ForeignKey(POSOrder, on_delete=models.PROTECT, related_name="returns")
    return_number = models.CharField(max_length=50, unique=True)
    state = models.CharField(max_length=20, choices=STATES, default="draft")
    refund_method = models.CharField(max_length=30, default="cash")
    total_refund = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    reason = models.TextField(blank=True)
    processed_by = models.UUIDField(null=True, blank=True)


class ReturnOrderLine(BaseModel):
    return_order = models.ForeignKey(ReturnOrder, on_delete=models.CASCADE, related_name="lines")
    original_line = models.ForeignKey(POSOrderLine, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    refund_amount = models.DecimalField(max_digits=14, decimal_places=2)
    reason = models.CharField(max_length=300, blank=True)
