from rest_framework import serializers

from .models import (
    LoyaltyCard, LoyaltyProgram, POSOrder, POSOrderLine,
    POSPayment, POSSession, POSTerminal, Promotion, ReturnOrder,
    ReturnOrderLine, Store,
)


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "name", "address", "phone", "email", "currency", "receipt_header", "receipt_footer", "tax_rate", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class POSTerminalSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = POSTerminal
        fields = ["id", "store", "store_name", "name", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class POSSessionSerializer(serializers.ModelSerializer):
    terminal_name = serializers.CharField(source="terminal.name", read_only=True)
    store_name = serializers.CharField(source="terminal.store.name", read_only=True)
    order_count = serializers.SerializerMethodField()
    total_sales = serializers.SerializerMethodField()

    class Meta:
        model = POSSession
        fields = [
            "id", "terminal", "terminal_name", "store_name", "cashier_id",
            "state", "opening_cash", "closing_cash", "expected_cash",
            "cash_difference", "opened_at", "closed_at", "notes",
            "order_count", "total_sales",
        ]
        read_only_fields = ["id", "opened_at", "expected_cash", "cash_difference"]

    def get_order_count(self, obj):
        return obj.orders.filter(state="paid").count()

    def get_total_sales(self, obj):
        from django.db.models import Sum
        return obj.orders.filter(state="paid").aggregate(t=Sum("total_amount"))["t"] or 0


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = [
            "id", "name", "promo_type", "discount_percent", "discount_amount",
            "min_order_amount", "min_qty", "product_id", "free_product_id",
            "date_start", "date_end", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class LoyaltyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyProgram
        fields = ["id", "name", "points_per_currency", "redemption_ratio", "min_points_redemption", "is_active"]
        read_only_fields = ["id"]


class LoyaltyCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyCard
        fields = ["id", "program", "customer_id", "card_number", "points_balance", "total_earned", "total_redeemed", "is_active", "created_at"]
        read_only_fields = ["id", "points_balance", "total_earned", "total_redeemed", "created_at"]


class POSOrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSOrderLine
        fields = [
            "id", "product_id", "variant_id", "product_name", "sku",
            "quantity", "unit_price", "discount_percent", "discount_amount",
            "subtotal", "lot_id", "serial_number", "notes",
        ]
        read_only_fields = ["id", "discount_amount", "subtotal"]


class POSPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSPayment
        fields = ["id", "method", "amount", "state", "reference", "mpesa_checkout_id", "created_at"]
        read_only_fields = ["id", "created_at"]


class POSOrderSerializer(serializers.ModelSerializer):
    lines = POSOrderLineSerializer(many=True, read_only=True)
    payments = POSPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = POSOrder
        fields = [
            "id", "corporate_id", "session", "order_number", "customer_id",
            "customer_name", "loyalty_card", "state", "subtotal",
            "discount_amount", "tax_amount", "total_amount", "amount_paid",
            "change_amount", "points_earned", "points_redeemed", "notes",
            "cashier_id", "created_at", "paid_at", "lines", "payments",
            # Invoice integration fields
            "invoice_id", "is_invoiced", "invoiced_at", "invoiced_by",
        ]
        read_only_fields = [
            "id", "order_number", "subtotal", "discount_amount", "tax_amount", 
            "total_amount", "created_at", "paid_at", "invoice_id", "is_invoiced", 
            "invoiced_at", "invoiced_by"
        ]


class ReturnOrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnOrderLine
        fields = ["id", "original_line", "quantity", "refund_amount", "reason"]
        read_only_fields = ["id"]


class ReturnOrderSerializer(serializers.ModelSerializer):
    lines = ReturnOrderLineSerializer(many=True, read_only=True)

    class Meta:
        model = ReturnOrder
        fields = ["id", "original_order", "return_number", "state", "refund_method", "total_refund", "reason", "created_at", "lines"]
        read_only_fields = ["id", "return_number", "created_at"]
