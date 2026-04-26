"""
Inventory Client for POS Service
Queries inventory service for product information
"""
import logging
import requests
from typing import Dict, List, Optional
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class InventoryClient:
    """
    Client for querying the Inventory Service
    Inventory is the single source of truth for products
    """
    
    def __init__(self):
        self.base_url = getattr(settings, 'INVENTORY_SERVICE_URL', 'http://inventory-backend:8000')
        # Use INVENTORY_SERVICE_SECRET for inter-service communication with inventory
        self.secret = getattr(settings, 'INVENTORY_SERVICE_SECRET', '')
        self.cache_ttl = 300  # 5 minutes
    
    def _get_headers(self, corporate_id: str) -> Dict:
        """Generate headers for service-to-service calls"""
        return {
            'X-Service-Key': self.secret,
            'X-Corporate-ID': str(corporate_id),
            'Content-Type': 'application/json',
        }
    
    def _get_cache_key(self, key_type: str, identifier: str, corporate_id: str) -> str:
        """Generate cache key"""
        return f"inventory:{key_type}:{corporate_id}:{identifier}"
    
    def get_product(self, product_id: str, corporate_id: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Get product details from inventory
        
        Args:
            product_id: Product UUID
            corporate_id: Corporate/tenant ID
            use_cache: Whether to use cached data (default: True)
            
        Returns:
            Product dict or None if not found
        """
        # Try cache first
        if use_cache:
            cache_key = self._get_cache_key('product', product_id, corporate_id)
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for product {product_id}")
                return cached
        
        # Fetch from inventory
        try:
            url = f"{self.base_url}/api/inventory/products/{product_id}/"
            logger.info(f"Fetching product {product_id} from {url} for corporate {corporate_id}")
            
            response = requests.get(
                url,
                headers=self._get_headers(corporate_id),
                timeout=5
            )
            
            logger.info(f"Inventory response status: {response.status_code}")
            
            if response.status_code == 404:
                logger.warning(f"Product {product_id} not found in inventory (404)")
                return None
            
            response.raise_for_status()
            product = response.json()
            
            logger.info(f"Successfully fetched product {product_id}: {product.get('name', 'Unknown')}")
            
            # Cache it
            if use_cache:
                cache_key = self._get_cache_key('product', product_id, corporate_id)
                cache.set(cache_key, product, self.cache_ttl)
            
            return product
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching product {product_id} from inventory at {self.base_url}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error fetching product {product_id} from inventory at {self.base_url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching product {product_id} from {self.base_url}: {str(e)}")
            return None
    
    def get_products_bulk(self, product_ids: List[str], corporate_id: str) -> List[Dict]:
        """
        Get multiple products at once
        
        Args:
            product_ids: List of product UUIDs
            corporate_id: Corporate/tenant ID
            
        Returns:
            List of product dicts
        """
        if not product_ids:
            return []
        
        try:
            response = requests.post(
                f"{self.base_url}/api/inventory/products/bulk/",
                json={'product_ids': product_ids},
                headers=self._get_headers(corporate_id),
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Cache individual products
            for product in data.get('products', []):
                cache_key = self._get_cache_key('product', product['id'], corporate_id)
                cache.set(cache_key, product, self.cache_ttl)
            
            return data.get('products', [])
            
        except Exception as e:
            logger.error(f"Error fetching products bulk: {str(e)}")
            return []
    
    def search_products(self, query: str, corporate_id: str) -> List[Dict]:
        """
        Search products by name, SKU, or barcode
        
        Args:
            query: Search term
            corporate_id: Corporate/tenant ID
            
        Returns:
            List of matching products
        """
        if not query:
            return []
        
        try:
            response = requests.get(
                f"{self.base_url}/api/inventory/products/search/",
                params={'q': query},
                headers=self._get_headers(corporate_id),
                timeout=5
            )
            
            response.raise_for_status()
            data = response.json()
            return data.get('products', [])
            
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    def get_stock_level(self, product_id: str, corporate_id: str) -> Optional[Dict]:
        """
        Get current stock level for a product
        
        Args:
            product_id: Product UUID
            corporate_id: Corporate/tenant ID
            
        Returns:
            Stock info dict or None
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/inventory/products/{product_id}/stock/",
                headers=self._get_headers(corporate_id),
                timeout=5
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching stock level: {str(e)}")
            return None
    
    def list_products_for_sale(self, corporate_id: str) -> List[Dict]:
        """
        List all products available for sale
        
        Args:
            corporate_id: Corporate/tenant ID
            
        Returns:
            List of products
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/inventory/products/for-sale/",
                headers=self._get_headers(corporate_id),
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            return data.get('products', [])
            
        except Exception as e:
            logger.error(f"Error listing products for sale: {str(e)}")
            return []
    
    def invalidate_cache(self, product_id: str, corporate_id: str):
        """
        Invalidate cached product data
        Call this when you know a product has been updated
        """
        cache_key = self._get_cache_key('product', product_id, corporate_id)
        cache.delete(cache_key)
        logger.debug(f"Invalidated cache for product {product_id}")
