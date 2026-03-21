from decimal import Decimal

from django.db import models
from django.utils import timezone

from pos_service.core.base_models import BaseModel


class Supplier(BaseModel):
    corporate_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=300)
    company_name = models.CharField(max_length=300, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="Kenya")
    payment_terms_days = models.PositiveIntegerField(default=30)
    currency = models.CharField(max_length=3, default="KES")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SupplierContact(BaseModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    position = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=False)


class PurchaseRequisition(BaseModel):
    STATES = [("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved"), ("cancelled", "Cancelled")]

    corporate_id = models.UUIDField(db_index=True)
    reference = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=20, choices=STATES, default="draft")
    requested_by = models.UUIDField()
    approved_by = models.UUIDField(null=True, blank=True)
    department = models.CharField(max_length=200, blank=True)
    reason = models.TextField(blank=True)
    required_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.reference


class PurchaseRequisitionLine(BaseModel):
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE, related_name="lines")
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=300)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    uom = models.CharField(max_length=50)
    estimated_unit_cost = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    notes = models.CharField(max_length=300, blank=True)


class RFQ(BaseModel):
    STATES = [("draft", "Draft"), ("sent", "Sent to Suppliers"), ("received", "Quotes Received"), ("cancelled", "Cancelled")]

    corporate_id = models.UUIDField(db_index=True)
    reference = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=20, choices=STATES, default="draft")
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return self.reference


class RFQLine(BaseModel):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="lines")
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=300)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    uom = models.CharField(max_length=50)


class RFQSupplierQuote(BaseModel):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="quotes")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    rfq_line = models.ForeignKey(RFQLine, on_delete=models.CASCADE, related_name="supplier_quotes")
    unit_price = models.DecimalField(max_digits=14, decimal_places=4)
    delivery_days = models.PositiveIntegerField(default=7)
    notes = models.CharField(max_length=300, blank=True)
    is_selected = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)


class PurchaseOrder(BaseModel):
    STATES = [
        ("draft", "Draft"),
        ("submitted", "Submitted for Approval"),
        ("approved", "Approved"),
        ("sent", "Sent to Supplier"),
        ("partial", "Partially Received"),
        ("received", "Fully Received"),
        ("billed", "Billed"),
        ("cancelled", "Cancelled"),
    ]

    corporate_id = models.UUIDField(db_index=True)
    po_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    state = models.CharField(max_length=20, choices=STATES, default="draft")
    rfq = models.ForeignKey(RFQ, on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.CharField(max_length=3, default="KES")
    payment_terms_days = models.PositiveIntegerField(default=30)
    expected_delivery_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    created_by = models.UUIDField(null=True, blank=True)
    approved_by = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.po_number

    def recalculate(self):
        lines = self.lines.all()
        self.subtotal = sum(l.subtotal for l in lines)
        self.tax_amount = sum(l.tax_amount for l in lines)
        self.total_amount = self.subtotal + self.tax_amount
        self.save()


class PurchaseOrderLine(BaseModel):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=300)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    received_qty = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0"))
    billed_qty = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0"))
    uom = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=14, decimal_places=4)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("16"))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    expected_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        self.tax_amount = self.subtotal * self.tax_rate / Decimal("100")
        super().save(*args, **kwargs)

    @property
    def pending_qty(self):
        return self.quantity - self.received_qty


class GoodsReceipt(BaseModel):
    STATES = [("draft", "Draft"), ("validated", "Validated"), ("cancelled", "Cancelled")]

    corporate_id = models.UUIDField(db_index=True)
    reference = models.CharField(max_length=100, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="receipts")
    state = models.CharField(max_length=20, choices=STATES, default="draft")
    warehouse_id = models.UUIDField(null=True, blank=True)
    location_id = models.UUIDField(null=True, blank=True)
    received_date = models.DateField()
    delivery_note = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    received_by = models.UUIDField(null=True, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.reference


class GoodsReceiptLine(BaseModel):
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="lines")
    po_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.PROTECT)
    quantity_received = models.DecimalField(max_digits=14, decimal_places=4)
    lot_number = models.CharField(max_length=150, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    quality_pass = models.BooleanField(default=True)
    notes = models.CharField(max_length=300, blank=True)


class SupplierBill(BaseModel):
    STATES = [("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved"), ("paid", "Paid"), ("cancelled", "Cancelled")]

    corporate_id = models.UUIDField(db_index=True)
    bill_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="bills")
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="bills")
    state = models.CharField(max_length=20, choices=STATES, default="draft")
    invoice_number = models.CharField(max_length=100, blank=True, help_text="Supplier's invoice number")
    invoice_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    notes = models.TextField(blank=True)

    @property
    def amount_due(self):
        return self.total_amount - self.amount_paid

    def __str__(self):
        return self.bill_number
