"""
Views for converting POS orders to invoices
"""

import logging
from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from pos_service.pos.models import POSOrder
from pos_service.pos.serializers import POSOrderSerializer
from pos_service.services.erp_client import ERPClient

logger = logging.getLogger(__name__)
erp_client = ERPClient()


@api_view(["POST"])
def convert_to_invoice(request, order_pk):
    """
    Convert a paid POS order to an invoice in the Accounting module
    
    Request Body:
    {
        "apply_tax": true,              # Whether to apply tax (default: true)
        "tax_rate_id": "uuid",          # Optional: specific tax rate UUID
        "due_days": 30,                 # Days until invoice is due (default: 30)
        "salesperson_id": "uuid",       # Required: salesperson user ID
        "comments": "string",           # Optional: invoice comments
        "terms": "string"               # Optional: payment terms
    }
    
    Response:
    {
        "success": true,
        "invoice_id": "uuid",
        "invoice_number": "INV-2026-001",
        "total": "1160.00",
        "order": {...}
    }
    """
    corporate_id = request.corporate_id
    
    try:
        # Get the order
        order = POSOrder.objects.select_related(
            "session__terminal__store"
        ).prefetch_related("lines", "payments").get(
            pk=order_pk,
            corporate_id=corporate_id
        )
    except POSOrder.DoesNotExist:
        return Response(
            {"error": "Order not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validate order state
    if order.state != "paid":
        return Response(
            {
                "error": "ORDER_NOT_PAID",
                "message": "Order must be paid before converting to invoice",
                "current_state": order.state
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if order.is_invoiced:
        return Response(
            {
                "error": "ALREADY_INVOICED",
                "message": f"Order has already been converted to invoice",
                "invoice_id": str(order.invoice_id) if order.invoice_id else None
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get request parameters
    apply_tax = request.data.get("apply_tax", True)
    tax_rate_id = request.data.get("tax_rate_id")
    due_days = request.data.get("due_days", 30)
    salesperson_id = request.data.get("salesperson_id")
    comments = request.data.get("comments", "")
    terms = request.data.get("terms", "Net 30")
    
    # Validate salesperson
    if not salesperson_id:
        return Response(
            {"error": "salesperson_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle customer
    accounting_customer_id = None
    
    if order.customer_id:
        # Get customer from CRM
        customer_data = erp_client.get_customer(str(corporate_id), str(order.customer_id))
        
        if not customer_data:
            return Response(
                {
                    "error": "CUSTOMER_NOT_FOUND",
                    "message": f"Customer {order.customer_id} not found in CRM"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create customer in Accounting
        accounting_customer_id = erp_client.get_or_create_accounting_customer(
            str(corporate_id),
            str(order.customer_id),
            customer_data
        )
        
        if not accounting_customer_id:
            return Response(
                {
                    "error": "CUSTOMER_CREATION_FAILED",
                    "message": "Failed to create customer in accounting system"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        # Walk-in customer - create generic customer
        walk_in_customer = {
            "first_name": "Walk-in",
            "last_name": "Customer",
            "email": "",
            "phone": "",
            "address": "",
            "city": "",
            "country": "Kenya",
        }
        
        # Try to get existing walk-in customer or create new one
        accounting_customer_id = erp_client.get_or_create_accounting_customer(
            str(corporate_id),
            "00000000-0000-0000-0000-000000000000",  # Special UUID for walk-in
            walk_in_customer
        )
        
        if not accounting_customer_id:
            return Response(
                {
                    "error": "CUSTOMER_CREATION_FAILED",
                    "message": "Failed to create walk-in customer"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Get default tax rate if not specified
    if apply_tax and not tax_rate_id:
        tax_rate = erp_client.get_default_tax_rate(str(corporate_id))
        if tax_rate:
            tax_rate_id = tax_rate["id"]
    
    # Prepare order data for invoice creation
    order_data = {
        "order_number": order.order_number,
        "subtotal": str(order.subtotal),
        "discount_amount": str(order.discount_amount),
        "lines": [
            {
                "product_id": str(line.product_id),
                "product_name": line.product_name,
                "sku": line.sku,
                "quantity": str(line.quantity),
                "unit_price": str(line.unit_price),
                "discount_amount": str(line.discount_amount),
                "subtotal": str(line.subtotal),
            }
            for line in order.lines.all()
        ],
    }
    
    # Create invoice
    invoice_data = erp_client.create_invoice(
        corporate_id=str(corporate_id),
        customer_id=accounting_customer_id,
        order_data=order_data,
        salesperson_id=salesperson_id,
        apply_tax=apply_tax,
        tax_rate_id=tax_rate_id,
        due_days=due_days,
        comments=comments,
        terms=terms,
    )
    
    if not invoice_data:
        return Response(
            {
                "error": "INVOICE_CREATION_FAILED",
                "message": "Failed to create invoice in accounting system"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Update order with invoice information
    order.invoice_id = invoice_data["id"]
    order.is_invoiced = True
    order.invoiced_at = timezone.now()
    order.invoiced_by = request.user_id
    order.state = "invoiced"
    
    # Update tax amount if tax was applied
    if apply_tax:
        order.tax_amount = Decimal(str(invoice_data.get("tax_total", "0")))
    
    order.save()
    
    logger.info(
        f"Order {order.order_number} converted to invoice {invoice_data.get('number')} "
        f"by user {request.user_id}"
    )
    
    return Response(
        {
            "success": True,
            "invoice_id": invoice_data["id"],
            "invoice_number": invoice_data.get("number"),
            "total": invoice_data.get("total"),
            "tax_applied": apply_tax,
            "tax_amount": invoice_data.get("tax_total", "0"),
            "order": POSOrderSerializer(order).data,
        },
        status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
def get_invoice_status(request, order_pk):
    """
    Get invoice status for a POS order
    
    Response:
    {
        "is_invoiced": true,
        "invoice_id": "uuid",
        "invoiced_at": "2026-04-15T10:30:00Z",
        "invoice_url": "/accounting/invoices/{id}/"
    }
    """
    corporate_id = request.corporate_id
    
    try:
        order = POSOrder.objects.get(pk=order_pk, corporate_id=corporate_id)
    except POSOrder.DoesNotExist:
        return Response(
            {"error": "Order not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response({
        "is_invoiced": order.is_invoiced,
        "invoice_id": str(order.invoice_id) if order.invoice_id else None,
        "invoiced_at": order.invoiced_at.isoformat() if order.invoiced_at else None,
        "invoiced_by": str(order.invoiced_by) if order.invoiced_by else None,
        "invoice_url": f"/api/accounting/invoices/{order.invoice_id}/" if order.invoice_id else None,
    })


@api_view(["GET"])
def list_uninvoiced_orders(request):
    """
    List all paid orders that haven't been converted to invoices
    
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
        state="paid",
        is_invoiced=False
    ).select_related("session__terminal__store")
    
    if customer_id:
        qs = qs.filter(customer_id=customer_id)
    
    if date_from:
        qs = qs.filter(paid_at__gte=date_from)
    
    if date_to:
        qs = qs.filter(paid_at__lte=date_to)
    
    # Get total count
    total_count = qs.count()
    
    # Apply pagination
    qs = qs.order_by("-paid_at")[offset:offset + limit]
    
    return Response({
        "count": total_count,
        "limit": limit,
        "offset": offset,
        "results": POSOrderSerializer(qs, many=True).data,
    })
