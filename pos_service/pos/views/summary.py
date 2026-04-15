"""
POS Dashboard Summary with period-over-period comparisons
"""
from decimal import Decimal
from datetime import timedelta
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from pos_service.pos.models import POSOrder, POSSession


@api_view(["GET"])
def pos_summary(request):
    """
    Returns POS metrics with period-over-period comparisons.
    Compares today vs yesterday for daily metrics.
    """
    cid = request.corporate_id
    
    # Current period (today)
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now
    
    # Previous period (yesterday)
    yesterday_start = today_start - timedelta(days=1)
    yesterday_end = today_start - timedelta(seconds=1)
    
    # Helper functions
    def calc_change(current, previous):
        if previous > 0:
            return round(float(((current - previous) / previous) * 100), 1)
        return 0.0
    
    def get_trend(change):
        if change > 0:
            return "up"
        elif change < 0:
            return "down"
        return "neutral"
    
    # Today's Sales
    todays_orders = POSOrder.objects.filter(
        corporate_id=cid,
        created_at__gte=today_start,
        created_at__lte=today_end,
        state__in=['paid', 'invoiced']
    )
    todays_sales = todays_orders.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    # Yesterday's Sales
    yesterday_orders = POSOrder.objects.filter(
        corporate_id=cid,
        created_at__gte=yesterday_start,
        created_at__lte=yesterday_end,
        state__in=['paid', 'invoiced']
    )
    yesterday_sales = yesterday_orders.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    sales_change = calc_change(float(todays_sales), float(yesterday_sales))
    
    # Transactions Today
    transactions_today = todays_orders.count()
    transactions_yesterday = yesterday_orders.count()
    transactions_change = calc_change(transactions_today, transactions_yesterday)
    
    # Average Order Value
    avg_order_value = todays_orders.aggregate(
        avg=Avg('total_amount')
    )['avg'] or Decimal('0')
    
    # Refunds Today
    refunds_today = POSOrder.objects.filter(
        corporate_id=cid,
        created_at__gte=today_start,
        state='returned'
    ).count()
    
    refunds_yesterday = POSOrder.objects.filter(
        corporate_id=cid,
        created_at__gte=yesterday_start,
        created_at__lte=yesterday_end,
        state='returned'
    ).count()
    
    refunds_change = calc_change(refunds_today, refunds_yesterday)
    
    # Active Sessions
    active_sessions = POSSession.objects.filter(
        terminal__store__corporate_id=cid,
        state='open'
    ).count()
    
    # Top Selling Items Today (optional)
    from django.db.models import F
    top_items = POSOrder.objects.filter(
        corporate_id=cid,
        created_at__gte=today_start,
        state__in=['paid', 'invoiced']
    ).values(
        'lines__product_name'
    ).annotate(
        quantity_sold=Sum('lines__quantity'),
        revenue=Sum(F('lines__quantity') * F('lines__unit_price'))
    ).order_by('-quantity_sold')[:5]
    
    return Response({
        "todays_sales": float(todays_sales),
        "todays_sales_previous": float(yesterday_sales),
        "todays_sales_change": sales_change,
        "todays_sales_trend": get_trend(sales_change),
        
        "transactions_today": transactions_today,
        "transactions_today_previous": transactions_yesterday,
        "transactions_today_change": transactions_change,
        "transactions_today_trend": get_trend(transactions_change),
        
        "average_order_value": float(avg_order_value),
        
        "refunds_today": refunds_today,
        "refunds_today_previous": refunds_yesterday,
        "refunds_today_change": refunds_change,
        "refunds_today_trend": get_trend(refunds_change),
        
        "active_sessions": active_sessions,
        "top_items": list(top_items),
    })
