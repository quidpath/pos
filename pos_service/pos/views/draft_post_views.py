"""
Draft/Post state machine views for POS Orders.
Provides save-draft, post (finalize), and auto-save endpoints.
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from ..models import POSOrder, POSOrderLine, POSSession


def validate_pos_order_for_posting(order):
    """Validate that a POS order can be posted (finalized)."""
    errors = []
    
    if not order.lines.exists():
        errors.append("Cannot finalize an order with no line items.")
    
    if order.total_amount <= 0:
        errors.append("Order total must be greater than zero.")
    
    if not order.session:
        errors.append("Order must be associated with a POS session.")
    
    if order.session.state != 'open':
        errors.append("Cannot finalize order - POS session is not open.")
    
    return errors


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_pos_order_draft(request):
    """
    Save a POS order as draft (held/parked order).
    Accepts partial data for orders being built.
    """
    data = request.data
    order_id = data.get('id')
    corporate_id = request.user.corporate_id
    
    try:
        with transaction.atomic():
            if order_id:
                # Update existing draft
                try:
                    order = POSOrder.objects.get(
                        id=order_id,
                        corporate_id=corporate_id
                    )
                except POSOrder.DoesNotExist:
                    return JsonResponse(
                        {"error": "Order not found"},
                        status=404
                    )
                
                # Check if editable
                if order.state != 'draft':
                    return JsonResponse(
                        {"error": f"Cannot edit order in {order.state} state"},
                        status=403
                    )
                
                # Update fields
                if 'customer_id' in data:
                    order.customer_id = data['customer_id']
                if 'customer_name' in data:
                    order.customer_name = data['customer_name']
                if 'notes' in data:
                    order.notes = data['notes']
                
                if not order.drafted_at:
                    order.drafted_at = timezone.now()
                
                order.save()
                
                # Update lines if provided
                if 'lines' in data:
                    order.lines.all().delete()
                    for line_data in data['lines']:
                        POSOrderLine.objects.create(
                            order=order,
                            product_id=line_data['product_id'],
                            product_name=line_data['product_name'],
                            quantity=Decimal(str(line_data['quantity'])),
                            unit_price=Decimal(str(line_data['unit_price'])),
                            discount_percent=Decimal(str(line_data.get('discount_percent', 0))),
                            sku=line_data.get('sku', ''),
                            variant_id=line_data.get('variant_id')
                        )
                    order.calculate_totals()
            
            else:
                # Create new draft order
                try:
                    session = POSSession.objects.get(
                        id=data['session_id'],
                        state='open'
                    )
                except POSSession.DoesNotExist:
                    return JsonResponse(
                        {"error": "Active POS session not found"},
                        status=400
                    )
                
                order = POSOrder.objects.create(
                    corporate_id=corporate_id,
                    session=session,
                    order_number=data.get('order_number', f"DRAFT-{timezone.now().timestamp()}"),
                    customer_id=data.get('customer_id'),
                    customer_name=data.get('customer_name', ''),
                    state='draft',
                    cashier_id=request.user.id,
                    drafted_at=timezone.now()
                )
                
                # Create lines
                if 'lines' in data:
                    for line_data in data['lines']:
                        POSOrderLine.objects.create(
                            order=order,
                            product_id=line_data['product_id'],
                            product_name=line_data['product_name'],
                            quantity=Decimal(str(line_data['quantity'])),
                            unit_price=Decimal(str(line_data['unit_price'])),
                            discount_percent=Decimal(str(line_data.get('discount_percent', 0))),
                            sku=line_data.get('sku', ''),
                            variant_id=line_data.get('variant_id')
                        )
                    order.calculate_totals()
            
            # Return complete order
            order.refresh_from_db()
            lines = list(order.lines.values())
            
            return JsonResponse({
                "success": True,
                "message": "Draft order saved successfully",
                "data": {
                    "id": str(order.id),
                    "order_number": order.order_number,
                    "state": order.state,
                    "subtotal": str(order.subtotal),
                    "tax_amount": str(order.tax_amount),
                    "total_amount": str(order.total_amount),
                    "drafted_at": order.drafted_at.isoformat() if order.drafted_at else None,
                    "lines": lines
                }
            })
    
    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_pos_order(request, order_id):
    """
    Finalize a POS order (transition from draft to paid).
    Validates all required fields and payment.
    """
    corporate_id = request.user.corporate_id
    data = request.data
    
    try:
        with transaction.atomic():
            try:
                order = POSOrder.objects.select_for_update().get(
                    id=order_id,
                    corporate_id=corporate_id
                )
            except POSOrder.DoesNotExist:
                return JsonResponse(
                    {"error": "Order not found"},
                    status=404
                )
            
            # Check if already posted
            if order.state == 'paid':
                return JsonResponse(
                    {"error": "Order is already finalized"},
                    status=400
                )
            
            # Validate
            errors = validate_pos_order_for_posting(order)
            if errors:
                return JsonResponse(
                    {"errors": errors},
                    status=400
                )
            
            # Process payment
            amount_paid = Decimal(str(data.get('amount_paid', 0)))
            if amount_paid < order.total_amount:
                return JsonResponse(
                    {"error": "Payment amount is less than order total"},
                    status=400
                )
            
            # Update order
            order.state = 'paid'
            order.amount_paid = amount_paid
            order.change_amount = amount_paid - order.total_amount
            order.paid_at = timezone.now()
            order.posted_at = timezone.now()
            order.posted_by = request.user.id
            order.save()
            
            # Update loyalty points if applicable
            if order.loyalty_card:
                program = order.loyalty_card.program
                points = order.total_amount * program.points_per_currency
                order.points_earned = points
                order.loyalty_card.points_balance += points
                order.loyalty_card.total_earned += points
                order.loyalty_card.save()
                order.save()
            
            return JsonResponse({
                "success": True,
                "message": "Order finalized successfully",
                "data": {
                    "id": str(order.id),
                    "order_number": order.order_number,
                    "state": order.state,
                    "total_amount": str(order.total_amount),
                    "amount_paid": str(order.amount_paid),
                    "change_amount": str(order.change_amount),
                    "posted_at": order.posted_at.isoformat(),
                    "posted_by": str(order.posted_by)
                }
            })
    
    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )


@csrf_exempt
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def auto_save_pos_order(request, order_id):
    """
    Auto-save POS order with minimal validation.
    Used for periodic saves while building an order.
    """
    corporate_id = request.user.corporate_id
    data = request.data
    
    try:
        try:
            order = POSOrder.objects.get(
                id=order_id,
                corporate_id=corporate_id
            )
        except POSOrder.DoesNotExist:
            return JsonResponse(
                {"error": "Order not found"},
                status=404
            )
        
        # Check if editable
        if order.state != 'draft':
            return JsonResponse(
                {"error": "Cannot auto-save non-draft order"},
                status=403
            )
        
        # Update simple fields
        if 'customer_name' in data:
            order.customer_name = data['customer_name']
        if 'notes' in data:
            order.notes = data['notes']
        
        order.save()
        
        return JsonResponse({
            "success": True,
            "message": "Auto-save successful"
        })
    
    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_draft_pos_orders(request):
    """List all draft (held/parked) orders for the current corporate."""
    corporate_id = request.user.corporate_id
    
    try:
        drafts = POSOrder.objects.filter(
            corporate_id=corporate_id,
            state='draft'
        ).values(
            'id', 'order_number', 'customer_name', 'total_amount',
            'drafted_at', 'created_at'
        )
        
        return JsonResponse({
            "success": True,
            "data": list(drafts)
        })
    
    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )
