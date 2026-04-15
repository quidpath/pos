"""
ERP Ecosystem Integration Client
Complete integration between POS, Inventory, Accounting, and CRM
"""
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


class ERPEcosystemClient:
    """
    Unified client for ERP ecosystem integration
    Handles the complete lifecycle: POS → Inventory → Accounting → CRM
    """
    
    def __init__(self):
        self.erp_url = settings.ERP_BACKEND_URL
        self.inventory_url = settings.INVENTORY_SERVICE_URL
        self.crm_url = settings.CRM_SERVICE_URL
        self.service_secret = settings.ERP_SERVICE_SECRET
        
    def _get_headers(self, corporate_id: str, user_id: str = None) -> Dict:
        """Generate service-to-service authentication headers"""
        headers = {
            'X-Service-Key': self.service_secret,
            'X-Corporate-ID': str(corporate_id),
            'Content-Type': 'application/json',
        }
        if user_id:
            headers['X-User-ID'] = str(user_id)
        return headers
    
    # ==================== CRM Integration ====================
    
    def get_customer(self, customer_id: str, corporate_id: str) -> Optional[Dict]:
        """Fetch customer from CRM"""
        try:
            url = f"{self.crm_url}/api/contacts/{customer_id}/"
            response = requests.get(
                url,
                headers=self._get_headers(corporate_id),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Customer {customer_id} not found in CRM")
                return None
            else:
                logger.error(f"Failed to fetch customer: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching customer from CRM: {str(e)}")
            return None
    
    def search_customers(self, query: str, corporate_id: str) -> List[Dict]:
        """Search customers in CRM by name, email, or phone"""
        try:
            url = f"{self.crm_url}/api/contacts/search/"
            response = requests.get(
                url,
                params={'q': query},
                headers=self._get_headers(corporate_id),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('results', [])
            return []
            
        except Exception as e:
            logger.error(f"Error searching customers: {str(e)}")
            return []
    
    def update_customer_ltv(self, customer_id: str, corporate_id: str, 
                           order_amount: Decimal) -> bool:
        """Update customer lifetime value in CRM"""
        try:
            url = f"{self.crm_url}/api/contacts/{customer_id}/update-ltv/"
            response = requests.post(
                url,
                json={'amount': str(order_amount)},
                headers=self._get_headers(corporate_id),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error updating customer LTV: {str(e)}")
            return False
    
    def create_crm_activity(self, customer_id: str, corporate_id: str, 
                           order_data: Dict) -> bool:
        """Create activity record in CRM for purchase"""
        try:
            url = f"{self.crm_url}/api/activities/"
            activity_data = {
                'activity_type': 'note',
                'status': 'done',
                'subject': f"Purchase - Order {order_data['order_number']}",
                'description': f"Customer made a purchase of {order_data['total_amount']}",
                'contact': customer_id,
                'done_at': datetime.now().isoformat(),
            }
            
            response = requests.post(
                url,
                json=activity_data,
                headers=self._get_headers(corporate_id),
                timeout=10
            )
            return response.status_code == 201
        except Exception as e:
            logger.error(f"Error creating CRM activity: {str(e)}")
            return False
    
    # ==================== Inventory Integration ====================
    
    def check_stock_availability(self, product_id: str, variant_id: Optional[str],
                                 quantity: Decimal, location_id: str,
                                 corporate_id: str) -> Tuple[bool, Decimal]:
        """
        Check if product is available in stock
        Returns: (is_available, available_quantity)
        """
        try:
            url = f"{self.inventory_url}/api/stock/check-availability/"
            data = {
                'product_id': str(product_id),
                'variant_id': str(variant_id) if variant_id else None,
                'quantity': str(quantity),
                'location_id': str(location_id),
            }
            
            response = requests.post(
                url,
                json=data,
                headers=self._get_headers(corporate_id),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['available'], Decimal(result['available_quantity'])
            return False, Decimal('0')
            
        except Exception as e:
            logger.error(f"Error checking stock availability: {str(e)}")
            return False, Decimal('0')
    
    def create_stock_move(self, order_data: Dict, corporate_id: str, 
                         user_id: str) -> Optional[str]:
        """
        Create stock move for POS sale (delivery to customer)
        Returns: stock_move_id
        """
        try:
            url = f"{self.inventory_url}/api/stock/moves/"
            
            # Create stock move for each order line
            move_ids = []
            for line in order_data['lines']:
                move_data = {
                    'reference': order_data['order_number'],
                    'move_type': 'delivery',
                    'product_id': str(line['product_id']),
                    'variant_id': str(line['variant_id']) if line.get('variant_id') else None,
                    'quantity': str(line['quantity']),
                    'location_from_id': order_data['location_id'],
                    'location_to_id': order_data['customer_location_id'],  # Customer location
                    'unit_cost': str(line['unit_price']),
                    'notes': f"POS Sale - Order {order_data['order_number']}",
                }
                
                response = requests.post(
                    url,
                    json=move_data,
                    headers=self._get_headers(corporate_id, user_id),
                    timeout=10
                )
                
                if response.status_code == 201:
                    move_id = response.json()['id']
                    move_ids.append(move_id)
                    
                    # Validate the move immediately
                    self.validate_stock_move(move_id, corporate_id, user_id)
                else:
                    logger.error(f"Failed to create stock move: {response.text}")
            
            return ','.join(move_ids) if move_ids else None
            
        except Exception as e:
            logger.error(f"Error creating stock move: {str(e)}")
            return None
    
    def validate_stock_move(self, move_id: str, corporate_id: str, 
                           user_id: str) -> bool:
        """Validate stock move to update inventory levels"""
        try:
            url = f"{self.inventory_url}/api/stock/moves/{move_id}/validate/"
            response = requests.post(
                url,
                headers=self._get_headers(corporate_id, user_id),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error validating stock move: {str(e)}")
            return False
    
    def get_product_valuation(self, product_id: str, corporate_id: str) -> Optional[Dict]:
        """Get product valuation (FIFO/Weighted Average cost)"""
        try:
            url = f"{self.inventory_url}/api/valuation/product/{product_id}/"
            response = requests.get(
                url,
                headers=self._get_headers(corporate_id),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting product valuation: {str(e)}")
            return None
    
    # ==================== Accounting Integration ====================
    
    def get_or_create_accounting_customer(self, crm_customer: Dict, 
                                         corporate_id: str) -> Optional[str]:
        """Get or create customer in Accounting module"""
        try:
            # Try to find existing customer by email
            url = f"{self.erp_url}/api/accounting/customers/"
            response = requests.get(
                url,
                params={'email': crm_customer['email']},
                headers=self._get_headers(corporate_id),
                timeout=10
            )
            
            if response.status_code == 200:
                customers = response.json().get('results', [])
                if customers:
                    return customers[0]['id']
            
            # Create new customer
            customer_data = {
                'category': 'individual',
                'first_name': crm_customer.get('first_name', ''),
                'last_name': crm_customer.get('last_name', ''),
                'email': crm_customer['email'],
                'phone': crm_customer.get('phone', ''),
                'mobile': crm_customer.get('mobile', ''),
                'address': crm_customer.get('address', ''),
                'city': crm_customer.get('city', ''),
                'country': crm_customer.get('country', 'Kenya'),
            }
            
            response = requests.post(
                url,
                json=customer_data,
                headers=self._get_headers(corporate_id),
                timeout=10
            )
            
            if response.status_code == 201:
                return response.json()['id']
            
            logger.error(f"Failed to create accounting customer: {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error creating accounting customer: {str(e)}")
            return None
    
    def create_invoice_from_order(self, order_data: Dict, corporate_id: str,
                                  user_id: str, apply_tax: bool = True) -> Optional[Dict]:
        """
        Create invoice in Accounting module from POS order
        This is where TAX is applied
        """
        try:
            url = f"{self.erp_url}/api/accounting/invoices/"
            
            # Get default tax rate (VAT 16%)
            tax_rate = self.get_default_tax_rate(corporate_id) if apply_tax else None
            
            # Calculate tax
            subtotal = Decimal(order_data['subtotal'])
            discount = Decimal(order_data['discount_amount'])
            taxable_amount = subtotal - discount
            
            if tax_rate:
                tax_amount = taxable_amount * (Decimal(tax_rate['rate']) / Decimal('100'))
                total = taxable_amount + tax_amount
            else:
                tax_amount = Decimal('0')
                total = taxable_amount
            
            # Prepare invoice data
            invoice_data = {
                'customer_id': order_data['accounting_customer_id'],
                'date': datetime.now().date().isoformat(),
                'due_date': (datetime.now().date() + timedelta(days=order_data.get('due_days', 30))).isoformat(),
                'salesperson_id': user_id,
                'comments': order_data.get('comments', f"Converted from POS Order {order_data['order_number']}"),
                'terms': order_data.get('terms', 'Net 30'),
                'purchase_order': order_data['order_number'],
                'sub_total': str(subtotal),
                'total_discount': str(discount),
                'tax_total': str(tax_amount),
                'total': str(total),
                'lines': []
            }
            
            # Add invoice lines
            for line in order_data['lines']:
                line_subtotal = Decimal(line['subtotal'])
                line_discount = Decimal(line['discount_amount'])
                line_taxable = line_subtotal - line_discount
                
                if tax_rate:
                    line_tax = line_taxable * (Decimal(tax_rate['rate']) / Decimal('100'))
                    line_total = line_taxable + line_tax
                else:
                    line_tax = Decimal('0')
                    line_total = line_taxable
                
                invoice_line = {
                    'description': line['product_name'],
                    'quantity': int(line['quantity']),
                    'unit_price': str(line['unit_price']),
                    'amount': str(line_subtotal),
                    'discount': str(line_discount),
                    'taxable_id': tax_rate['id'] if tax_rate else None,
                    'tax_amount': str(line_tax),
                    'sub_total': str(line_taxable),
                    'total': str(line_total),
                }
                invoice_data['lines'].append(invoice_line)
            
            # Create invoice
            response = requests.post(
                url,
                json=invoice_data,
                headers=self._get_headers(corporate_id, user_id),
                timeout=15
            )
            
            if response.status_code == 201:
                invoice = response.json()
                logger.info(f"Invoice {invoice['number']} created from order {order_data['order_number']}")
                return invoice
            else:
                logger.error(f"Failed to create invoice: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}", exc_info=True)
            return None
    
    def post_invoice(self, invoice_id: str, corporate_id: str, 
                    user_id: str) -> bool:
        """Post invoice and create journal entry"""
        try:
            url = f"{self.erp_url}/api/accounting/invoices/{invoice_id}/post/"
            response = requests.post(
                url,
                headers=self._get_headers(corporate_id, user_id),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error posting invoice: {str(e)}")
            return False
    
    def get_default_tax_rate(self, corporate_id: str) -> Optional[Dict]:
        """Get default VAT 16% tax rate"""
        try:
            url = f"{self.erp_url}/api/accounting/tax-rates/"
            response = requests.get(
                url,
                params={'name': 'general_rated'},
                headers=self._get_headers(corporate_id),
                timeout=10
            )
            
            if response.status_code == 200:
                rates = response.json().get('results', [])
                if rates:
                    return rates[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching tax rate: {str(e)}")
            return None
    
    # ==================== Complete Order Processing ====================
    
    @transaction.atomic
    def process_complete_order_flow(self, order, user_id: str, 
                                    user_email: str, user_name: str,
                                    convert_to_invoice: bool = False) -> Dict:
        """
        Complete ERP ecosystem flow for a POS order:
        1. Update Inventory (stock deduction)
        2. Update CRM (customer LTV, activity)
        3. Create Invoice (if requested)
        4. Create Journal Entry (if invoice posted)
        5. Send Receipt Email
        
        Returns: {
            'success': bool,
            'inventory_updated': bool,
            'crm_updated': bool,
            'invoice_created': bool,
            'journal_created': bool,
            'email_sent': bool,
            'invoice_id': str,
            'errors': List[str]
        }
        """
        result = {
            'success': False,
            'inventory_updated': False,
            'crm_updated': False,
            'invoice_created': False,
            'journal_created': False,
            'email_sent': False,
            'invoice_id': None,
            'errors': []
        }
        
        try:
            corporate_id = str(order.corporate_id)
            
            # 1. Update Inventory
            logger.info(f"Processing inventory for order {order.order_number}")
            order_data = {
                'order_number': order.order_number,
                'location_id': str(order.session.terminal.store.id),  # Store location
                'customer_location_id': 'CUSTOMER',  # Virtual customer location
                'lines': [
                    {
                        'product_id': str(line.product_id),
                        'variant_id': str(line.variant_id) if line.variant_id else None,
                        'quantity': str(line.quantity),
                        'unit_price': str(line.unit_price),
                        'subtotal': str(line.subtotal),
                        'discount_amount': str(line.discount_amount),
                        'product_name': line.product_name,
                    }
                    for line in order.lines.all()
                ]
            }
            
            stock_move_id = self.create_stock_move(order_data, corporate_id, user_id)
            if stock_move_id:
                result['inventory_updated'] = True
                logger.info(f"Inventory updated for order {order.order_number}")
            else:
                result['errors'].append("Failed to update inventory")
            
            # 2. Update CRM
            if order.customer_id:
                logger.info(f"Updating CRM for customer {order.customer_id}")
                
                # Update LTV
                ltv_updated = self.update_customer_ltv(
                    str(order.customer_id),
                    corporate_id,
                    order.total_amount
                )
                
                # Create activity
                activity_created = self.create_crm_activity(
                    str(order.customer_id),
                    corporate_id,
                    {
                        'order_number': order.order_number,
                        'total_amount': str(order.total_amount),
                    }
                )
                
                if ltv_updated and activity_created:
                    result['crm_updated'] = True
                    logger.info(f"CRM updated for customer {order.customer_id}")
                else:
                    result['errors'].append("Failed to update CRM")
            
            # 3. Create Invoice (if requested)
            if convert_to_invoice:
                logger.info(f"Converting order {order.order_number} to invoice")
                
                # Get or create accounting customer
                accounting_customer_id = None
                if order.customer_id:
                    crm_customer = self.get_customer(str(order.customer_id), corporate_id)
                    if crm_customer:
                        accounting_customer_id = self.get_or_create_accounting_customer(
                            crm_customer,
                            corporate_id
                        )
                
                if accounting_customer_id:
                    order_data['accounting_customer_id'] = accounting_customer_id
                    order_data['subtotal'] = str(order.subtotal)
                    order_data['discount_amount'] = str(order.discount_amount)
                    
                    invoice = self.create_invoice_from_order(
                        order_data,
                        corporate_id,
                        user_id,
                        apply_tax=True
                    )
                    
                    if invoice:
                        result['invoice_created'] = True
                        result['invoice_id'] = invoice['id']
                        
                        # Update order
                        order.invoice_id = invoice['id']
                        order.is_invoiced = True
                        order.invoiced_at = datetime.now()
                        order.invoiced_by = user_id
                        order.state = 'invoiced'
                        order.save()
                        
                        logger.info(f"Invoice {invoice['number']} created")
                        
                        # 4. Post invoice to create journal entry
                        if self.post_invoice(invoice['id'], corporate_id, user_id):
                            result['journal_created'] = True
                            logger.info(f"Journal entry created for invoice {invoice['number']}")
                        else:
                            result['errors'].append("Failed to create journal entry")
                    else:
                        result['errors'].append("Failed to create invoice")
                else:
                    result['errors'].append("Failed to get/create accounting customer")
            
            # 5. Send Receipt Email
            if order.customer_id:
                crm_customer = self.get_customer(str(order.customer_id), corporate_id)
                if crm_customer and crm_customer.get('email'):
                    from pos_service.services.receipt_email_service import ReceiptEmailService
                    
                    email_sent = ReceiptEmailService.send_receipt(
                        order,
                        crm_customer['email'],
                        user_email,
                        user_name
                    )
                    
                    if email_sent:
                        result['email_sent'] = True
                        logger.info(f"Receipt emailed to {crm_customer['email']}")
                    else:
                        result['errors'].append("Failed to send receipt email")
            
            # Overall success
            result['success'] = (
                result['inventory_updated'] and
                (not convert_to_invoice or result['invoice_created'])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in complete order flow: {str(e)}", exc_info=True)
            result['errors'].append(str(e))
            return result
