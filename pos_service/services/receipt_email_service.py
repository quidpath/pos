"""
Receipt Email Service
Sends digital receipts to customers via user's email (not system email)
"""
import logging
from decimal import Decimal
from typing import Optional
from datetime import datetime

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


class ReceiptEmailService:
    """Service for sending POS receipts via email"""
    
    @staticmethod
    def send_receipt(order, customer_email: str, user_email: str, user_name: str) -> bool:
        """
        Send receipt email to customer from user's email
        
        Args:
            order: POSOrder instance
            customer_email: Customer's email address
            user_email: User's email (sender)
            user_name: User's full name
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Prepare receipt data
            receipt_data = {
                'order': order,
                'order_number': order.order_number,
                'customer_name': order.customer_name or 'Valued Customer',
                'date': order.paid_at or order.created_at,
                'cashier_name': user_name,
                'store': order.session.terminal.store,
                'lines': order.lines.all(),
                'subtotal': order.subtotal,
                'discount': order.discount_amount,
                'tax': order.tax_amount,
                'total': order.total_amount,
                'amount_paid': order.amount_paid,
                'change': order.change_amount,
                'payments': order.payments.all(),
                'points_earned': order.points_earned,
                'points_redeemed': order.points_redeemed,
            }
            
            # Render HTML email template
            html_content = render_to_string('pos/receipt_email.html', receipt_data)
            
            # Render plain text version
            text_content = ReceiptEmailService._generate_text_receipt(receipt_data)
            
            # Create email
            subject = f'Receipt for Order {order.order_number}'
            
            email = EmailMessage(
                subject=subject,
                body=text_content,
                from_email=f'{user_name} <{user_email}>',  # User's email as sender
                to=[customer_email],
                reply_to=[user_email],
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send(fail_silently=False)
            
            logger.info(
                f"Receipt sent successfully for order {order.order_number} "
                f"from {user_email} to {customer_email}"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send receipt for order {order.order_number}: {str(e)}",
                exc_info=True
            )
            return False
    
    @staticmethod
    def _generate_text_receipt(data: dict) -> str:
        """Generate plain text receipt"""
        store = data['store']
        lines_text = []
        
        for line in data['lines']:
            lines_text.append(
                f"{line.product_name} x{line.quantity} @ {line.unit_price} = {line.subtotal}"
            )
        
        receipt = f"""
{store.name}
{store.address}
{store.phone}
{store.email}

{'='*50}
RECEIPT
{'='*50}

Order Number: {data['order_number']}
Date: {data['date'].strftime('%Y-%m-%d %H:%M:%S')}
Cashier: {data['cashier_name']}
Customer: {data['customer_name']}

{'='*50}
ITEMS
{'='*50}

{chr(10).join(lines_text)}

{'='*50}
Subtotal:        {data['subtotal']}
Discount:       -{data['discount']}
Tax:            +{data['tax']}
{'='*50}
TOTAL:           {data['total']}
{'='*50}

Amount Paid:     {data['amount_paid']}
Change:          {data['change']}

"""
        
        if data['points_earned'] > 0:
            receipt += f"\nLoyalty Points Earned: {data['points_earned']}\n"
        
        if data['points_redeemed'] > 0:
            receipt += f"Loyalty Points Redeemed: {data['points_redeemed']}\n"
        
        receipt += f"\n{store.receipt_footer}\n"
        receipt += "\nThank you for your business!\n"
        
        return receipt
