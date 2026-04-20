"""
Product Views for POS
Queries inventory service for product information
"""
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from pos_service.services.inventory_client import InventoryClient

logger = logging.getLogger(__name__)


@api_view(['GET'])
def search_products(request):
    """
    Search products from inventory
    
    GET /api/pos/products/search/?q=query
    """
    try:
        query = request.GET.get('q', '').strip()
        if not query:
            return Response({'error': 'Query parameter "q" is required'}, status=400)
        
        inventory = InventoryClient()
        products = inventory.search_products(query, request.corporate_id)
        
        return Response({
            'count': len(products),
            'products': products
        })
        
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def get_product(request, product_id):
    """
    Get single product from inventory
    
    GET /api/pos/products/{product_id}/
    """
    try:
        inventory = InventoryClient()
        product = inventory.get_product(product_id, request.corporate_id)
        
        if not product:
            return Response({'error': 'Product not found'}, status=404)
        
        return Response(product)
        
    except Exception as e:
        logger.error(f"Error getting product: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def list_products_for_sale(request):
    """
    List all products available for sale
    
    GET /api/pos/products/
    """
    try:
        inventory = InventoryClient()
        products = inventory.list_products_for_sale(request.corporate_id)
        
        return Response({
            'count': len(products),
            'products': products
        })
        
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def get_products_bulk(request):
    """
    Get multiple products at once
    
    POST /api/pos/products/bulk/
    Body: {"product_ids": ["uuid1", "uuid2"]}
    """
    try:
        product_ids = request.data.get('product_ids', [])
        if not product_ids:
            return Response({'error': 'product_ids is required'}, status=400)
        
        inventory = InventoryClient()
        products = inventory.get_products_bulk(product_ids, request.corporate_id)
        
        return Response({
            'count': len(products),
            'products': products
        })
        
    except Exception as e:
        logger.error(f"Error getting products bulk: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def check_stock(request, product_id):
    """
    Check stock level for a product
    
    GET /api/pos/products/{product_id}/stock/
    """
    try:
        inventory = InventoryClient()
        stock = inventory.get_stock_level(product_id, request.corporate_id)
        
        if not stock:
            return Response({'error': 'Stock information not available'}, status=404)
        
        return Response(stock)
        
    except Exception as e:
        logger.error(f"Error checking stock: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)
