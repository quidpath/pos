"""
ERP Client for POS service to communicate with main quidpath backend
Handles customer lookups and invoice creation
"""

import logging
import os
from typing import Dict, List, Optional
from decimal import Decimal

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class ERPClient:
    """Client for communicating with main ERP backend"""

    def __init__(self):
        self.base_url = os.environ.get("ERP_BACKEND_URL", "http://django-backend:8000")
        self.service_secret = os.environ.get("ERP_SERVICE_SECRET", "")
        self.timeout = 10  # seconds

        # Setup session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_headers(self, corporate_id: str) -> Dict[str, str]:
        """Get headers for service-to-service communication"""
        return {
            "Content-Type": "application/json",
            "X-Service-Key": self.service_secret,
            "X-Corporate-ID": corporate_id,
        }

    def get_customer(self, corporate_id: str, customer_id: str) -> Optional[Dict]:
        """
        Get customer details from CRM
        
        Args:
            corporate_id: Corporate UUID
            customer_id: Contact UUID from CRM
            
        Returns:
            Customer data dict or None if not found
        """
        try:
            url = f"{self.base_url}/api/crm/contacts/{customer_id}/"
            response = self.session.get(
                url,
                headers=self._get_headers(corporate_id),
                timeout=self.timeout,
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Customer {customer_id} not found in CRM")
                return None
            else:
                logger.error(f"Failed to fetch customer: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching customer {customer_id}: {e}")
            return None

    def search_customers(self, corporate_id: str, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for customers in CRM
        
        Args:
            corporate_id: Corporate UUID
            query: Search query (name, email, phone)
            limit: Max results to return
            
        Returns:
            List of customer data dicts
        """
        try:
            url = f"{self.base_url}/api/crm/contacts/"
            params = {"search": query, "limit": limit}
            response = self.session.get(
                url,
                headers=self._get_headers(corporate_id),
                params=params,
                timeout=self.timeout,
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                logger.error(f"Failed to search customers: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching customers: {e}")
            return []

    def get_or_create_accounting_customer(
        self, 
        corporate_id: str, 
        contact_id: str,
        contact_data: Dict
    ) -> Optional[str]:
        """
        Get or create customer in Accounting module
        
        Args:
            corporate_id: Corporate UUID
            contact_id: CRM Contact UUID
            contact_data: Contact data from CRM
            
        Returns:
            Accounting Customer UUID or None
        """
        try:
            # First try to get existing customer
            url = f"{self.base_url}/api/accounting/customers/"
            params = {"crm_contact_id": contact_id}
            response = self.session.get(
                url,
                headers=self._get_headers(corporate_id),
                params=params,
                timeout=self.timeout,
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    return results[0]["id"]
            
            # Create new customer
            customer_payload = {
                "name": f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip(),
                "email": contact_data.get("email", ""),
                "phone": contact_data.get("phone", "") or contact_data.get("mobile", ""),
                "address": contact_data.get("address", ""),
                "city": contact_data.get("city", ""),
                "country": contact_data.get("country", "Kenya"),
                "crm_contact_id": contact_id,
            }
            
            response = self.session.post(
                url,
                headers=self._get_headers(corporate_id),
                json=customer_payload,
                timeout=self.timeout,
            )
            
            if response.status_code in [200, 201]:
                return response.json()["id"]
            else:
                logger.error(f"Failed to create accounting customer: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting/creating accounting customer: {e}")
            return None

    def create_invoice(
        self,
        corporate_id: str,
        customer_id: str,
        order_data: Dict,
        salesperson_id: str,
        apply_tax: bool = True,
        tax_rate_id: Optional[str] = None,
        due_days: int = 30,
        comments: str = "",
        terms: str = "",
    ) -> Optional[Dict]:
        """
        Create invoice in Accounting module from POS order
        
        Args:
            corporate_id: Corporate UUID
            customer_id: Accounting Customer UUID
            order_data: POS order data
            salesperson_id: User ID of salesperson
            apply_tax: Whether to apply tax
            tax_rate_id: Tax rate UUID (optional, uses default if not provided)
            due_days: Days until invoice is due
            comments: Invoice comments
            terms: Payment terms
            
        Returns:
            Invoice data dict or None
        """
        try:
            from datetime import date, timedelta
            
            invoice_date = date.today()
            due_date = invoice_date + timedelta(days=due_days)
            
            # Calculate totals
            subtotal = Decimal(str(order_data.get("subtotal", "0")))
            discount = Decimal(str(order_data.get("discount_amount", "0")))
            taxable_amount = subtotal - discount
            
            # Apply tax if requested
            tax_total = Decimal("0")
            if apply_tax:
                # Default to 16% VAT if no tax rate specified
                tax_rate = Decimal("16.0")
                tax_total = taxable_amount * tax_rate / Decimal("100")
            
            total = taxable_amount + tax_total
            
            # Prepare invoice payload
            invoice_payload = {
                "customer": customer_id,
                "date": invoice_date.isoformat(),
                "due_date": due_date.isoformat(),
                "status": "DRAFT",
                "payment_status": "unpaid",
                "comments": comments or f"Converted from POS Order {order_data.get('order_number', '')}",
                "terms": terms or "Net 30",
                "salesperson": salesperson_id,
                "sub_total": str(subtotal),
                "total_discount": str(discount),
                "tax_total": str(tax_total),
                "total": str(total),
                "lines": [],
            }
            
            # Add invoice lines
            for line in order_data.get("lines", []):
                invoice_line = {
                    "description": line.get("product_name", ""),
                    "quantity": int(line.get("quantity", 1)),
                    "unit_price": str(line.get("unit_price", "0")),
                    "amount": str(Decimal(str(line.get("quantity", 1))) * Decimal(str(line.get("unit_price", "0")))),
                    "discount": str(line.get("discount_amount", "0")),
                    "sub_total": str(line.get("subtotal", "0")),
                    "total": str(line.get("subtotal", "0")),
                }
                
                # Add tax rate if specified
                if apply_tax and tax_rate_id:
                    invoice_line["taxable"] = tax_rate_id
                    # Calculate tax for this line
                    line_taxable = Decimal(str(invoice_line["sub_total"]))
                    line_tax = line_taxable * Decimal("16.0") / Decimal("100")
                    invoice_line["tax_amount"] = str(line_tax)
                    invoice_line["total"] = str(line_taxable + line_tax)
                
                invoice_payload["lines"].append(invoice_line)
            
            # Create invoice
            url = f"{self.base_url}/api/accounting/invoices/"
            response = self.session.post(
                url,
                headers=self._get_headers(corporate_id),
                json=invoice_payload,
                timeout=self.timeout,
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Created invoice for POS order {order_data.get('order_number')}")
                return response.json()
            else:
                logger.error(f"Failed to create invoice: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating invoice: {e}", exc_info=True)
            return None

    def get_default_tax_rate(self, corporate_id: str) -> Optional[Dict]:
        """
        Get default tax rate (VAT 16%) for corporate
        
        Args:
            corporate_id: Corporate UUID
            
        Returns:
            Tax rate data dict or None
        """
        try:
            url = f"{self.base_url}/api/accounting/tax-rates/"
            params = {"name": "general_rated"}
            response = self.session.get(
                url,
                headers=self._get_headers(corporate_id),
                params=params,
                timeout=self.timeout,
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    return results[0]
            
            logger.warning(f"Default tax rate not found for corporate {corporate_id}")
            return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching default tax rate: {e}")
            return None

    def post_invoice(
        self,
        invoice_id: str,
        corporate_id: str,
        user_id: str,
        payment_account_id: Optional[str] = None
    ) -> bool:
        """
        Post invoice to create journal entry
        
        Args:
            invoice_id: Invoice UUID
            corporate_id: Corporate UUID
            user_id: User ID posting the invoice
            payment_account_id: Account where payment was received (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/accounting/invoices/{invoice_id}/post/"
            payload = {}
            
            if payment_account_id:
                payload['payment_account_id'] = payment_account_id
            
            response = self.session.post(
                url,
                headers=self._get_headers(corporate_id),
                json=payload,
                timeout=self.timeout,
            )
            
            if response.status_code == 200:
                logger.info(f"Posted invoice {invoice_id}")
                return True
            else:
                logger.error(f"Failed to post invoice: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting invoice: {e}")
            return False
    
    def update_customer_ltv(
        self,
        corporate_id: str,
        customer_id: str,
        amount: Decimal
    ) -> bool:
        """
        Update customer lifetime value in CRM
        
        Args:
            corporate_id: Corporate UUID
            customer_id: Contact UUID
            amount: Amount to add to LTV
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/crm/contacts/{customer_id}/update-ltv/"
            payload = {'amount': str(amount)}
            
            response = self.session.post(
                url,
                headers=self._get_headers(corporate_id),
                json=payload,
                timeout=self.timeout,
            )
            
            return response.status_code == 200
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating customer LTV: {e}")
            return False
    
    def create_crm_activity(
        self,
        corporate_id: str,
        customer_id: str,
        activity_data: Dict
    ) -> bool:
        """
        Create activity record in CRM for purchase
        
        Args:
            corporate_id: Corporate UUID
            customer_id: Contact UUID
            activity_data: Activity data (order_number, total_amount)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import datetime
            
            url = f"{self.base_url}/api/crm/activities/"
            payload = {
                'activity_type': 'note',
                'status': 'done',
                'subject': f"Purchase - Order {activity_data.get('order_number', '')}",
                'description': f"Customer made a purchase of {activity_data.get('total_amount', '0')}",
                'contact': customer_id,
                'done_at': datetime.now().isoformat(),
            }
            
            response = self.session.post(
                url,
                headers=self._get_headers(corporate_id),
                json=payload,
                timeout=self.timeout,
            )
            
            return response.status_code == 201
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating CRM activity: {e}")
            return False
