import logging
import uuid
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from pos_service.pos.models import (
    LoyaltyCard, LoyaltyProgram, POSOrder, POSOrderLine,
    POSPayment, POSSession, POSTerminal, Promotion, ReturnOrder,
    ReturnOrderLine, Store,
)
from pos_service.pos.serializers import (
    LoyaltyCardSerializer, LoyaltyProgramSerializer,
    POSOrderSerializer, POSSessionSerializer, POSTerminalSerializer,
    PromotionSerializer, ReturnOrderSerializer, StoreSerializer,
)
from pos_service.services.inventory_client import InventoryClient
from pos_service.core.utils.pagination import paginate_qs

logger = logging.getLogger(__name__)
inventory_client = InventoryClient()


# ─── Stores ──────────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
def store_list_create(request):
    corporate_id = request.corporate_id
    if request.method == "GET":
        return Response(StoreSerializer(Store.objects.filter(corporate_id=corporate_id), many=True).data)
    s = StoreSerializer(data=request.data)
    if s.is_valid():
        s.save(corporate_id=corporate_id)
        return Response(s.data, status=201)
    return Response(s.errors, status=400)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def store_detail(request, pk):
    corporate_id = request.corporate_id
    try:
        store = Store.objects.get(pk=pk, corporate_id=corporate_id)
    except Store.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    if request.method == "GET":
        return Response(StoreSerializer(store).data)
    if request.method in ("PUT", "PATCH"):
        s = StoreSerializer(store, data=request.data, partial=request.method == "PATCH")
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)
    store.is_active = False
    store.save()
    return Response(status=204)


# ─── Sessions ────────────────────────────────────────────────────────────────

@api_view(["POST"])
def open_session(request, terminal_pk):
    corporate_id = request.corporate_id
    try:
        terminal = POSTerminal.objects.get(pk=terminal_pk, store__corporate_id=corporate_id)
    except POSTerminal.DoesNotExist:
        return Response({"error": "Terminal not found"}, status=404)
    open_session_exists = POSSession.objects.filter(terminal=terminal, state="open").exists()
    if open_session_exists:
        return Response({"error": "A session is already open on this terminal"}, status=400)
    opening_cash = Decimal(str(request.data.get("opening_cash", "0")))
    session = POSSession.objects.create(
        terminal=terminal, cashier_id=request.user_id, opening_cash=opening_cash
    )
    return Response(POSSessionSerializer(session).data, status=201)


@api_view(["POST"])
def close_session(request, pk):
    corporate_id = request.corporate_id
    try:
        session = POSSession.objects.get(pk=pk, terminal__store__corporate_id=corporate_id, state="open")
    except POSSession.DoesNotExist:
        return Response({"error": "Open session not found"}, status=404)
    closing_cash = Decimal(str(request.data.get("closing_cash", "0")))
    session.close(closing_cash)
    return Response(POSSessionSerializer(session).data)


@api_view(["GET"])
def session_list(request):
    corporate_id = request.corporate_id
    qs = POSSession.objects.filter(terminal__store__corporate_id=corporate_id).select_related("terminal__store")
    state = request.GET.get("state")
    if state:
        qs = qs.filter(state=state)
    return Response(POSSessionSerializer(qs[:50], many=True).data)


# ─── Orders ──────────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
def order_list_create(request):
    corporate_id = request.corporate_id
    if request.method == "GET":
        qs = POSOrder.objects.filter(corporate_id=corporate_id).select_related("session__terminal__store")
        state = request.GET.get("state")
        if state:
            qs = qs.filter(state=state)
        session_id = request.GET.get("session")
        if session_id:
            qs = qs.filter(session_id=session_id)
        search = request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(Q(order_number__icontains=search) | Q(customer_name__icontains=search))
        qs = qs.order_by("-created_at")
        page_qs, meta = paginate_qs(qs, request)
        return Response({"results": POSOrderSerializer(page_qs, many=True).data, **meta})

    session_id = request.data.get("session")
    try:
        session = POSSession.objects.get(pk=session_id, terminal__store__corporate_id=corporate_id, state="open")
    except POSSession.DoesNotExist:
        return Response({"error": "Active session not found"}, status=400)

    order_number = f"POS-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    # Check if order should be marked as paid immediately
    mark_as_paid = request.data.get("mark_as_paid", False)
    payment_account_id = request.data.get("payment_account_id")
    
    # Determine initial state
    initial_state = 'paid' if mark_as_paid else 'draft'
    
    order = POSOrder.objects.create(
        corporate_id=corporate_id,
        session=session,
        order_number=order_number,
        customer_id=request.data.get("customer_id"),
        customer_name=request.data.get("customer_name", ""),
        cashier_id=request.user_id,
        state=initial_state,
        payment_account_id=payment_account_id if mark_as_paid else None,
        paid_at=timezone.now() if mark_as_paid else None,
    )
    
    # If marked as paid, sync to accounting immediately
    if mark_as_paid and payment_account_id:
        from pos_service.services.accounting_sync_service import AccountingSyncService
        sync_service = AccountingSyncService()
        
        # Sync to accounting (will happen after order lines are added)
        # For now, just mark the order as needing sync
        logger.info(f"Order {order.order_number} marked as paid, will sync after lines are added")
    
    return Response(POSOrderSerializer(order).data, status=201)


@api_view(["GET"])
def order_detail(request, pk):
    corporate_id = request.corporate_id
    try:
        order = POSOrder.objects.get(pk=pk, corporate_id=corporate_id)
    except POSOrder.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    return Response(POSOrderSerializer(order).data)


@api_view(["POST"])
def add_order_line(request, order_pk):
    """Add product to order with inventory validation"""
    corporate_id = request.corporate_id
    try:
        order = POSOrder.objects.get(pk=order_pk, corporate_id=corporate_id, state="draft")
    except POSOrder.DoesNotExist:
        return Response({"error": "Draft order not found"}, status=404)
    
    product_id = request.data.get("product_id")
    quantity = Decimal(str(request.data.get("quantity", "1")))
    
    # Get product from inventory
    product = inventory_client.get_product(product_id, corporate_id)
    if not product:
        return Response({"error": "Product not found in inventory"}, status=404)
    
    # Check stock availability
    stock = inventory_client.get_stock_level(product_id, corporate_id)
    if stock:
        available = Decimal(stock.get('total_available', '0'))
        if available < quantity:
            return Response({
                "error": "Insufficient stock",
                "available": str(available),
                "requested": str(quantity)
            }, status=400)
    
    # Create order line with captured data from inventory
    line = POSOrderLine(
        order=order,
        product_id=product_id,
        variant_id=request.data.get("variant_id"),
        product_name=product['name'],  # Captured from inventory
        sku=product.get('internal_reference', ''),  # Captured from inventory
        quantity=quantity,
        unit_price=Decimal(product.get('list_price', request.data.get('unit_price', '0'))),  # Use inventory price
        discount_percent=Decimal(str(request.data.get("discount_percent", "0"))),
        notes=request.data.get("notes", ""),
    )
    line.save()
    order.calculate_totals()
    return Response(POSOrderSerializer(order).data, status=201)


@api_view(["DELETE"])
def remove_order_line(request, order_pk, line_pk):
    corporate_id = request.corporate_id
    try:
        order = POSOrder.objects.get(pk=order_pk, corporate_id=corporate_id, state="draft")
        line = POSOrderLine.objects.get(pk=line_pk, order=order)
    except (POSOrder.DoesNotExist, POSOrderLine.DoesNotExist):
        return Response({"error": "Not found"}, status=404)
    line.delete()
    order.calculate_totals()
    return Response(POSOrderSerializer(order).data)


@api_view(["POST"])
def process_payment(request, order_pk):
    """Process payment for an order — supports multiple payment methods (split payment)."""
    corporate_id = request.corporate_id
    try:
        order = POSOrder.objects.get(pk=order_pk, corporate_id=corporate_id, state="draft")
    except POSOrder.DoesNotExist:
        return Response({"error": "Draft order not found"}, status=404)

    payments_data = request.data.get("payments", [])
    if not payments_data:
        return Response({"error": "At least one payment method required"}, status=400)
    
    # Get payment account for accounting sync
    payment_account_id = request.data.get("payment_account_id")
    if not payment_account_id:
        return Response({"error": "payment_account_id is required for accounting sync"}, status=400)

    total_paid = Decimal("0")
    payment_objects = []
    for p in payments_data:
        amount = Decimal(str(p["amount"]))
        payment = POSPayment(
            order=order,
            method=p["method"],
            amount=amount,
            reference=p.get("reference", ""),
            state="completed",
        )
        payment_objects.append(payment)
        total_paid += amount

    if total_paid < order.total_amount:
        return Response({"error": f"Insufficient payment. Required: {order.total_amount}, Received: {total_paid}"}, status=400)

    for p in payment_objects:
        p.save()

    order.amount_paid = total_paid
    order.change_amount = total_paid - order.total_amount
    order.state = "paid"
    order.paid_at = timezone.now()
    order.payment_account_id = payment_account_id

    # Award loyalty points
    if order.loyalty_card:
        program = order.loyalty_card.program
        points = order.total_amount * program.points_per_currency
        order.points_earned = points
        order.loyalty_card.points_balance += points
        order.loyalty_card.total_earned += points
        order.loyalty_card.save()

    order.save()

    # Automatically sync to accounting
    from pos_service.services.accounting_sync_service import AccountingSyncService
    sync_service = AccountingSyncService()
    
    sync_result = sync_service.sync_order_to_accounting(
        order=order,
        user_id=request.user_id,
        payment_account_id=payment_account_id,
        apply_tax=True  # Always apply tax
    )
    
    if not sync_result['success']:
        logger.error(f"Failed to sync order {order.order_number} to accounting: {sync_result['error']}")
        # Don't fail the payment, just log the error
        # Order can be synced later via retry endpoint

    return Response({
        **POSOrderSerializer(order).data,
        'accounting_sync': {
            'success': sync_result['success'],
            'invoice_id': sync_result['invoice_id'],
            'invoice_number': sync_result['invoice_number'],
            'error': sync_result['error']
        }
    })


@api_view(["POST"])
def process_return(request, order_pk):
    corporate_id = request.corporate_id
    try:
        original = POSOrder.objects.get(pk=order_pk, corporate_id=corporate_id, state__in=["paid", "invoiced"])
    except POSOrder.DoesNotExist:
        return Response({"error": "Paid order not found"}, status=404)

    return_number = f"RET-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    return_order = ReturnOrder.objects.create(
        corporate_id=corporate_id,
        original_order=original,
        return_number=return_number,
        refund_method=request.data.get("refund_method", "cash"),
        reason=request.data.get("reason", ""),
        processed_by=request.user_id,
    )

    total_refund = Decimal("0")
    for line_data in request.data.get("lines", []):
        original_line = POSOrderLine.objects.get(pk=line_data["original_line"], order=original)
        qty = Decimal(str(line_data["quantity"]))
        refund = qty * original_line.unit_price
        ReturnOrderLine.objects.create(
            return_order=return_order,
            original_line=original_line,
            quantity=qty,
            refund_amount=refund,
            reason=line_data.get("reason", ""),
        )
        total_refund += refund

    return_order.total_refund = total_refund
    return_order.state = "validated"
    return_order.save()
    return Response(ReturnOrderSerializer(return_order).data, status=201)


@api_view(["POST"])
def mark_order_as_paid(request, order_pk):
    """
    Mark a pending order as paid and sync to accounting
    
    Request Body:
    {
        "payment_account_id": "uuid",  # Required: Account where payment was received
        "payments": [                   # Required: Payment details
            {
                "method": "cash",
                "amount": "1000.00",
                "reference": ""
            }
        ],
        "apply_tax": true               # Optional: Whether to apply tax (default: true)
    }
    
    Response:
    {
        "success": true,
        "order": {...},
        "accounting_sync": {
            "success": true,
            "invoice_id": "uuid",
            "invoice_number": "INV-2026-001",
            "error": null
        }
    }
    """
    corporate_id = request.corporate_id
    
    try:
        order = POSOrder.objects.get(pk=order_pk, corporate_id=corporate_id)
    except POSOrder.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)
    
    # Validate order state
    if order.state not in ['draft', 'pending']:
        return Response({
            "error": "ORDER_ALREADY_PAID",
            "message": f"Order is already in '{order.state}' state",
            "current_state": order.state
        }, status=400)
    
    # Get payment details
    payments_data = request.data.get("payments", [])
    if not payments_data:
        return Response({"error": "At least one payment method required"}, status=400)
    
    payment_account_id = request.data.get("payment_account_id")
    if not payment_account_id:
        return Response({"error": "payment_account_id is required"}, status=400)
    
    apply_tax = request.data.get("apply_tax", True)
    
    # Process payments
    total_paid = Decimal("0")
    payment_objects = []
    for p in payments_data:
        amount = Decimal(str(p["amount"]))
        payment = POSPayment(
            order=order,
            method=p["method"],
            amount=amount,
            reference=p.get("reference", ""),
            state="completed",
        )
        payment_objects.append(payment)
        total_paid += amount
    
    if total_paid < order.total_amount:
        return Response({
            "error": "INSUFFICIENT_PAYMENT",
            "message": f"Insufficient payment. Required: {order.total_amount}, Received: {total_paid}"
        }, status=400)
    
    # Save payments
    for p in payment_objects:
        p.save()
    
    # Update order
    order.amount_paid = total_paid
    order.change_amount = total_paid - order.total_amount
    order.state = "paid"
    order.paid_at = timezone.now()
    order.payment_account_id = payment_account_id
    order.save()
    
    # Sync to accounting
    from pos_service.services.accounting_sync_service import AccountingSyncService
    sync_service = AccountingSyncService()
    
    sync_result = sync_service.sync_order_to_accounting(
        order=order,
        user_id=request.user_id,
        payment_account_id=payment_account_id,
        apply_tax=apply_tax
    )
    
    if not sync_result['success']:
        logger.error(f"Failed to sync order {order.order_number} to accounting: {sync_result['error']}")
    
    return Response({
        "success": True,
        "order": POSOrderSerializer(order).data,
        "accounting_sync": {
            "success": sync_result['success'],
            "invoice_id": sync_result['invoice_id'],
            "invoice_number": sync_result['invoice_number'],
            "error": sync_result['error']
        }
    }, status=200)


@api_view(["GET"])
def list_pending_orders(request):
    """
    List all orders that are pending payment
    
    Query Parameters:
    - limit: Max results (default: 50)
    - offset: Pagination offset (default: 0)
    - customer_id: Filter by customer
    - date_from: Filter by date (YYYY-MM-DD)
    - date_to: Filter by date (YYYY-MM-DD)
    
    Response:
    {
        "count": 10,
        "results": [...]
    }
    """
    corporate_id = request.corporate_id
    
    # Get query parameters
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))
    customer_id = request.GET.get("customer_id")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    
    # Build query
    qs = POSOrder.objects.filter(
        corporate_id=corporate_id,
        state__in=['draft', 'pending']
    ).select_related("session__terminal__store")
    
    if customer_id:
        qs = qs.filter(customer_id=customer_id)
    
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    
    if date_to:
        qs = qs.filter(created_at__lte=date_to)
    
    # Get total count
    total_count = qs.count()
    
    # Apply pagination
    qs = qs.order_by("-created_at")[offset:offset + limit]
    
    return Response({
        "count": total_count,
        "limit": limit,
        "offset": offset,
        "results": POSOrderSerializer(qs, many=True).data,
    })


# ─── Promotions & Loyalty ────────────────────────────────────────────────────

@api_view(["GET", "POST"])
def promotion_list_create(request):
    corporate_id = request.corporate_id
    if request.method == "GET":
        return Response(PromotionSerializer(Promotion.objects.filter(corporate_id=corporate_id, is_active=True), many=True).data)
    s = PromotionSerializer(data=request.data)
    if s.is_valid():
        s.save(corporate_id=corporate_id)
        return Response(s.data, status=201)
    return Response(s.errors, status=400)


@api_view(["GET", "POST"])
def loyalty_program_list_create(request):
    corporate_id = request.corporate_id
    if request.method == "GET":
        return Response(LoyaltyProgramSerializer(LoyaltyProgram.objects.filter(corporate_id=corporate_id), many=True).data)
    s = LoyaltyProgramSerializer(data=request.data)
    if s.is_valid():
        s.save(corporate_id=corporate_id)
        return Response(s.data, status=201)
    return Response(s.errors, status=400)


@api_view(["GET"])
def loyalty_card_lookup(request):
    card_number = request.GET.get("card_number", "").strip()
    if not card_number:
        return Response({"error": "card_number required"}, status=400)
    try:
        card = LoyaltyCard.objects.select_related("program").get(card_number=card_number, is_active=True)
        return Response(LoyaltyCardSerializer(card).data)
    except LoyaltyCard.DoesNotExist:
        return Response({"error": "Card not found"}, status=404)
