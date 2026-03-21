from rest_framework import serializers

from .models import (
    GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderLine,
    PurchaseRequisition, PurchaseRequisitionLine, RFQ, RFQLine,
    RFQSupplierQuote, Supplier, SupplierBill, SupplierContact,
)


class SupplierContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierContact
        fields = ["id", "name", "email", "phone", "position", "is_primary"]
        read_only_fields = ["id"]


class SupplierSerializer(serializers.ModelSerializer):
    contacts = SupplierContactSerializer(many=True, read_only=True)

    class Meta:
        model = Supplier
        fields = [
            "id", "name", "company_name", "tax_id", "email", "phone", "address",
            "city", "country", "payment_terms_days", "currency", "notes", "is_active",
            "created_at", "contacts",
        ]
        read_only_fields = ["id", "created_at"]


class PurchaseRequisitionLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisitionLine
        fields = ["id", "product_id", "product_name", "quantity", "uom", "estimated_unit_cost", "notes"]
        read_only_fields = ["id"]


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    lines = PurchaseRequisitionLineSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseRequisition
        fields = [
            "id", "corporate_id", "reference", "state", "requested_by", "approved_by",
            "department", "reason", "required_date", "created_at", "updated_at", "lines",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RFQLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFQLine
        fields = ["id", "product_id", "product_name", "quantity", "uom"]
        read_only_fields = ["id"]


class RFQSupplierQuoteSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = RFQSupplierQuote
        fields = ["id", "rfq", "supplier", "supplier_name", "rfq_line", "unit_price", "delivery_days", "notes", "is_selected", "received_at"]
        read_only_fields = ["id", "received_at"]


class RFQSerializer(serializers.ModelSerializer):
    lines = RFQLineSerializer(many=True, read_only=True)
    quotes = RFQSupplierQuoteSerializer(many=True, read_only=True)

    class Meta:
        model = RFQ
        fields = ["id", "reference", "state", "requisition", "deadline", "notes", "created_at", "lines", "quotes"]
        read_only_fields = ["id", "created_at"]


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    pending_qty = serializers.DecimalField(max_digits=14, decimal_places=4, read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = [
            "id", "product_id", "product_name", "quantity", "received_qty", "billed_qty",
            "uom", "unit_price", "tax_rate", "tax_amount", "subtotal", "expected_date", "pending_qty",
        ]
        read_only_fields = ["id", "received_qty", "billed_qty", "tax_amount", "subtotal"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "corporate_id", "po_number", "supplier", "supplier_name", "state",
            "currency", "payment_terms_days", "expected_delivery_date",
            "subtotal", "tax_amount", "total_amount", "notes",
            "created_by", "approved_by", "created_at", "updated_at", "lines",
        ]
        read_only_fields = ["id", "po_number", "subtotal", "tax_amount", "total_amount", "created_at", "updated_at"]


class GoodsReceiptLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsReceiptLine
        fields = ["id", "po_line", "quantity_received", "lot_number", "expiry_date", "quality_pass", "notes"]
        read_only_fields = ["id"]


class GoodsReceiptSerializer(serializers.ModelSerializer):
    lines = GoodsReceiptLineSerializer(many=True, read_only=True)

    class Meta:
        model = GoodsReceipt
        fields = [
            "id", "corporate_id", "reference", "purchase_order", "state",
            "warehouse_id", "location_id", "received_date", "delivery_note", "notes",
            "received_by", "validated_at", "created_at", "lines",
        ]
        read_only_fields = ["id", "validated_at", "created_at"]


class SupplierBillSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    amount_due = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = SupplierBill
        fields = [
            "id", "corporate_id", "bill_number", "supplier", "supplier_name",
            "purchase_order", "state", "invoice_number", "invoice_date", "due_date",
            "subtotal", "tax_amount", "total_amount", "amount_paid", "amount_due",
            "notes", "created_at",
        ]
        read_only_fields = ["id", "bill_number", "created_at", "amount_due"]
