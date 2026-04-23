"""
Product Sync View for POS
Ensures products are available in inventory before use
"""
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from pos_service.services.inventory_client import InventoryClient
from pos_service.services.erp_client import ERPClient

logger = logging.getLogger(__name__)


@api_view(['POST'])
def sync_product_to_inventory(request, product_id):
    """
    Sync a product from accounting/ERP to inventory
    This ensures the product is available for POS use
    
    POST /api/pos/products/{product_id}/sync/
    """
    try:
        corporate_id = request.corporate_id
        
        # Check if product already exists in inventory
        inventory_client = InventoryClient()
        existing_product = inventory_client.get_product(product_id, corporate_id, use_cache=False)
        
        if existing_product:
            return Response({
                'success': True,
                'message': 'Product already exists in inventory',
                'product': existing_product
            })
        
        # Get product from ERP/Accounting
        erp_client = ERPClient()
        erp_product = erp_client.get_product(corporate_id, product_id)
        
        if not erp_product:
            return Response({
                'success': False,
                'error': 'Product not found in ERP system'
            }, status=404)
        
        # Sync to inventory
        sync_result = erp_client.sync_product_to_inventory(corporate_id, product_id, erp_product)
        
        if sync_result.get('success'):
            # Invalidate cache
            inventory_client.invalidate_cache(product_id, corporate_id)
            
            return Response({
                'success': True,
                'message': 'Product synced to inventory successfully',
                'product': sync_result.get('product')
            })
        else:
            return Response({
                'success': False,
                'error': sync_result.get('error', 'Failed to sync product')
            }, status=500)
        
    except Exception as e:
        logger.error(f"Error syncing product: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
def auto_sync_products(request):
    """
    Auto-sync products from order items
    Called before order creation to ensure all products are available
    
    POST /api/pos/products/auto-sync/
    Body: {"product_ids": ["uuid1", "uuid2"]}
    """
    try:
        corporate_id = request.corporate_id
        product_ids = request.data.get('product_ids', [])
        
        if not product_ids:
            return Response({'error': 'product_ids is required'}, status=400)
        
        inventory_client = InventoryClient()
        erp_client = ERPClient()
        
        results = {
            'synced': [],
            'already_exists': [],
            'failed': [],
            'products': []
        }
        
        for product_id in product_ids:
            try:
                # Check if exists
                existing = inventory_client.get_product(product_id, corporate_id, use_cache=False)
                
                if existing:
                    results['already_exists'].append(product_id)
                    results['products'].append(existing)
                    continue
                
                # Get from ERP
                erp_product = erp_client.get_product(corporate_id, product_id)
                
                if not erp_product:
                    results['failed'].append({
                        'product_id': product_id,
                        'error': 'Not found in ERP'
                    })
                    continue
                
                # Sync to inventory
                sync_result = erp_client.sync_product_to_inventory(corporate_id, product_id, erp_product)
                
                if sync_result.get('success'):
                    results['synced'].append(product_id)
                    results['products'].append(sync_result.get('product'))
                    inventory_client.invalidate_cache(product_id, corporate_id)
                else:
                    results['failed'].append({
                        'product_id': product_id,
                        'error': sync_result.get('error', 'Sync failed')
                    })
                    
            except Exception as e:
                logger.error(f"Error syncing product {product_id}: {str(e)}")
                results['failed'].append({
                    'product_id': product_id,
                    'error': str(e)
                })
        
        return Response({
            'success': True,
            'results': results,
            'summary': {
                'total': len(product_ids),
                'synced': len(results['synced']),
                'already_exists': len(results['already_exists']),
                'failed': len(results['failed'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error in auto-sync: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)
