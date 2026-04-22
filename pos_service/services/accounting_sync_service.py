"""
Accounting Sync Service
Automatically syncs POS orders to accounting when marked as paid
"""
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Optional

from django.utils import timezone
from django.db import transaction

from pos_service.services.erp_client import ERPClient
from pos_service.services.inventory_client import InventoryClient

logger = logging.getLogger(__name__)


class AccountingSyncService:
    """
    Service to automatically sync POS orders to accounting
    Creates invoices and journal entries when orders are marked as paid
    """
    
    def __init__(self):
        self.erp_client = ERPClient()
        self.inventory_client = InventoryClient()
    
    @transaction.atomic
    def sync_order_to_accounting(self, order, user_id: str, 
                                 payment_account_id: str = None,
                                 apply_tax: bool = True) -> Dict:
        """
        Sync a paid order to accounting
        
        Args:
            order: POSOrder instance
            user_id: User ID who is syncing
            payment_account_id: Account where payment was received
            apply_tax: Whether to apply tax (default: True)
        
        Returns:
            {
                'success': bool,
                'invoice_id': str,
                'invoice_number': str,
                'journal_entry_id': str,
                'error': str
            }
        """
        result = {
            'success': False,
            'invoice_id': None,
            'invoice_number': None,
            'journal_entry_id': None,
            'error': None
        }
        
        try:
            corporate_id = str(order.corporate_id)
            
            # Check if already synced
            if order.accounting_synced and order.invoice_id:
                logger.warning(f"Order {order.order_number} already synced to accounting")
                result['success'] = True
                result['invoice_id'] = str(order.invoice_id)
                return result
            
            # 1. Get or create customer in accounting
            accounting_customer_id = self._get_or_create_customer(order, corporate_id)
            if not accounting_customer_id:
                result['error'] = "Failed to create customer in accounting"
                return result
            
            # 2. Get default tax rate if applying tax
            tax_rate_id = None
            if apply_tax:
                tax_rate = self.erp_client.get_default_tax_rate(corporate_id)
                if tax_rate:
                    tax_rate_id = tax_rate['id']
            
            # 3. Prepare order data
            order_data = {
                'order_number': order.order_number,
                'subtotal': str(order.subtotal),
                'discount_amount': str(order.discount_amount),
                'lines': [
                    {
                        'product_id': str(line.product_id),
                        'product_name': line.product_name,
                        'sku': line.sku,
                        'quantity': str(line.quantity),
                        'unit_price': str(line.unit_price),
                        'discount_amount': str(line.discount_amount),
                        'subtotal': str(line.subtotal),
                    }
                    for line in order.lines.all()
                ]
            }
            
            # 4. Create invoice
            invoice_data = self.erp_client.create_invoice(
                corporate_id=corporate_id,
                customer_id=accounting_customer_id,
                order_data=order_data,
                salesperson_id=user_id,
                apply_tax=apply_tax,
                tax_rate_id=tax_rate_id,
                due_days=0,  # Immediate payment (already paid)
                comments=f"POS Order {order.order_number} - Paid via POS",
                terms="Paid",
            )
            
            if not invoice_data:
                result['error'] = "Failed to create invoice"
                return result
            
            result['invoice_id'] = invoice_data['id']
            result['invoice_number'] = invoice_data.get('number')
            
            # 5. Post invoice to create journal entry
            journal_created = self.erp_client.post_invoice(
                invoice_id=invoice_data['id'],
                corporate_id=corporate_id,
                user_id=user_id,
                payment_account_id=payment_account_id  # Pass payment account
            )
            
            if journal_created:
                result['journal_entry_id'] = invoice_data.get('journal_entry_id')
            
            # 6. Update order
            order.invoice_id = invoice_data['id']
            order.is_invoiced = True
            order.invoiced_at = timezone.now()
            order.invoiced_by = user_id
            order.state = 'invoiced'
            order.accounting_synced = True
            order.accounting_sync_error = ''
            
            # Update tax amount if tax was applied
            if apply_tax:
                order.tax_amount = Decimal(str(invoice_data.get('tax_total', '0')))
            
            # Store payment account
            if payment_account_id:
                order.payment_account_id = payment_account_id
            
            order.save()
            
            result['success'] = True
            
            logger.info(
                f"Order {order.order_number} synced to accounting. "
                f"Invoice: {result['invoice_number']}, "
                f"Journal Entry: {result['journal_entry_id']}"
            )
            
            # 7. Update inventory (create stock moves)
            self._update_inventory(order, corporate_id, user_id)
            
            # 8. Update CRM if customer exists
            if order.customer_id:
                self._update_crm(order, corporate_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error syncing order to accounting: {str(e)}", exc_info=True)
            result['error'] = str(e)
            
            # Update order with error
            order.accounting_sync_error = str(e)
            order.save()
            
            return result
    
    def _get_or_create_customer(self, order, corporate_id: str) -> Optional[str]:
        """Get or create customer in accounting"""
        try:
            if order.customer_id:
                # Get customer from CRM
                customer_data = self.erp_client.get_customer(corporate_id, str(order.customer_id))
                
                if customer_data:
                    # Get or create in accounting
                    return self.erp_client.get_or_create_accounting_customer(
                        corporate_id,
                        str(order.customer_id),
                        customer_data
                    )
            
            # Walk-in customer
            walk_in_customer = {
                'first_name': order.customer_name or 'Walk-in',
                'last_name': 'Customer',
                'email': '',
                'phone': '',
                'address': '',
                'city': '',
                'country': 'Kenya',
            }
            
            return self.erp_client.get_or_create_accounting_customer(
                corporate_id,
                '00000000-0000-0000-0000-000000000000',  # Special UUID for walk-in
                walk_in_customer
            )
            
        except Exception as e:
            logger.error(f"Error getting/creating customer: {str(e)}")
            return None
    
    def _update_inventory(self, order, corporate_id: str, user_id: str):
        """Update inventory with stock moves"""
        try:
            for line in order.lines.all():
                try:
                    # Create delivery stock move
                    self.inventory_client.create_stock_move({
                        'corporate_id': corporate_id,
                        'reference': order.order_number,
                        'move_type': 'delivery',
                        'product_id': str(line.product_id),
                        'variant_id': str(line.variant_id) if line.variant_id else None,
                        'quantity': str(line.quantity),
                        'state': 'done',
                    })
                except Exception as e:
                    logger.warning(f"Could not update inventory for line {line.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error updating inventory: {str(e)}")
    
    def _update_crm(self, order, corporate_id: str):
        """Update CRM with customer activity"""
        try:
            # Update customer lifetime value
            self.erp_client.update_customer_ltv(
                corporate_id,
                str(order.customer_id),
                order.total_amount
            )
            
            # Create activity record
            self.erp_client.create_crm_activity(
                corporate_id,
                str(order.customer_id),
                {
                    'order_number': order.order_number,
                    'total_amount': str(order.total_amount),
                }
            )
        except Exception as e:
            logger.error(f"Error updating CRM: {str(e)}")
    
    def retry_failed_syncs(self, corporate_id: str, user_id: str, limit: int = 50) -> Dict:
        """
        Retry syncing orders that failed to sync to accounting
        
        Returns:
            {
                'total': int,
                'success': int,
                'failed': int,
                'errors': List[str]
            }
        """
        from pos_service.pos.models import POSOrder
        
        result = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Get orders that are paid but not synced
            orders = POSOrder.objects.filter(
                corporate_id=corporate_id,
                state='paid',
                accounting_synced=False
            ).order_by('paid_at')[:limit]
            
            result['total'] = orders.count()
            
            for order in orders:
                sync_result = self.sync_order_to_accounting(
                    order,
                    user_id,
                    payment_account_id=order.payment_account_id
                )
                
                if sync_result['success']:
                    result['success'] += 1
                else:
                    result['failed'] += 1
                    result['errors'].append(
                        f"Order {order.order_number}: {sync_result['error']}"
                    )
            
            logger.info(
                f"Retry sync completed: {result['success']}/{result['total']} successful"
            )
            
        except Exception as e:
            logger.error(f"Error in retry_failed_syncs: {str(e)}", exc_info=True)
            result['errors'].append(str(e))
        
        return result
