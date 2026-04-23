# Product Not Found Issue - Fix Guide

## Problem
When creating a POS order, getting error:
```json
{
  "error": "Product 4e120f08-4a8d-4479-9467-8b8ea878ef45 not found in inventory"
}
```

Even though the product appears in the dropdown.

## Root Cause

### Frontend vs Backend Mismatch
**Frontend** (OrderModal):
- Calls: `/api/inventory/products/integrated/list/`
- Gets products from **multiple sources** (Inventory + Accounting + other services)
- Shows ALL products across the system

**Backend** (POS Service):
- Calls: `/api/inventory/products/{id}/`
- Only gets products from **Inventory service database**
- Product must exist in inventory_product table

### Why This Happens
1. Product was created in Accounting module
2. Product appears in "integrated" list (combines all services)
3. Product was NOT synced to Inventory service database
4. POS tries to fetch from Inventory service → 404 Not Found

## Solutions

### Solution 1: Use POS Products Endpoint (RECOMMENDED)
The POS service has its own product query endpoints that should be used by the frontend.

**Change frontend to use:**
```typescript
// Instead of:
inventoryService.getProducts()

// Use:
posService.getProducts()  // This calls /api/pos/products/
```

**POS Product Endpoints:**
- `GET /api/pos/products/` - List products for sale
- `GET /api/pos/products/search/?q=query` - Search products
- `GET /api/pos/products/{id}/` - Get single product
- `GET /api/pos/products/bulk/` - Get multiple products
- `GET /api/pos/products/{id}/stock/` - Check stock

These endpoints are specifically designed for POS and handle the integration correctly.

### Solution 2: Ensure Product Sync
Make sure products are synced to inventory service when created.

**In Accounting Module** (when creating product):
```python
# After creating product in accounting
from inventory_client import InventoryClient

inventory_client = InventoryClient()
inventory_client.sync_product(product_id, corporate_id)
```

**Bulk Sync Existing Products:**
```bash
# Run this command to sync all products
python manage.py sync_products_to_inventory
```

### Solution 3: Make POS Use Integrated Endpoint
Update POS inventory client to use integrated endpoint:

**File:** `pos/pos_service/services/inventory_client.py`

```python
def get_product(self, product_id: str, corporate_id: str, use_cache: bool = True) -> Optional[Dict]:
    # Change from:
    url = f"{self.base_url}/api/inventory/products/{product_id}/"
    
    # To:
    url = f"{self.base_url}/api/inventory/products/integrated/{product_id}/"
```

## Immediate Workaround

### For Users
1. Go to Inventory module
2. Find the product by name
3. Click "Sync to Services" or "Re-sync"
4. Try creating POS order again

### For Developers
Run this SQL to check if product exists in inventory:

```sql
-- Check if product exists in inventory service
SELECT id, name, internal_reference, is_active
FROM inventory_product
WHERE id = '4e120f08-4a8d-4479-9467-8b8ea878ef45';

-- If not found, sync it from accounting
INSERT INTO inventory_product (id, name, internal_reference, ...)
SELECT id, name, sku, ...
FROM accounting_product
WHERE id = '4e120f08-4a8d-4479-9467-8b8ea878ef45';
```

## Prevention

### 1. Update Frontend to Use POS Endpoints
**File:** `qpfrontend/src/modules/pos/modals/OrderModal.tsx`

```typescript
// Change this:
import { useProducts } from '@/hooks/useInventory';
const { data: productsData } = useProducts();

// To this:
import { usePOSProducts } from '@/hooks/usePOS';
const { data: productsData } = usePOSProducts();
```

### 2. Create usePOS Hook
**File:** `qpfrontend/src/hooks/usePOS.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import posService from '@/services/posService';

export function usePOSProducts(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ['pos', 'products', params],
    queryFn: async () => {
      const { data } = await posService.getProducts(params);
      return data;
    },
    staleTime: 30_000,
  });
}
```

### 3. Add Product Sync on Creation
Whenever a product is created in any module, automatically sync to inventory:

```python
# In product creation view
@transaction.atomic
def create_product(request):
    # Create product
    product = Product.objects.create(...)
    
    # Sync to inventory
    try:
        inventory_client = InventoryClient()
        inventory_client.sync_product(product.id, corporate_id)
    except Exception as e:
        logger.warning(f"Failed to sync product to inventory: {e}")
        # Don't fail the creation, just log
    
    return Response(...)
```

## Testing

### Test Product Availability
```bash
# Test from POS service
curl -H "X-Corporate-ID: 91e59699-41b6-403b-8ff0-a449ae6cd6ac" \
     -H "X-Service-Key: your-secret" \
     http://inventory-backend:8000/api/inventory/products/4e120f08-4a8d-4479-9467-8b8ea878ef45/

# Should return product details, not 404
```

### Test POS Product Endpoint
```bash
# Test POS products endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://pos-backend:8000/api/pos/products/

# Should return list of products available for sale
```

## Recommended Implementation Order

1. **Immediate** (5 min):
   - Add better error message showing inventory URL
   - Add logging to see which endpoint is being called
   - ✅ Already done in commit 4ab0fef

2. **Short Term** (1 hour):
   - Update frontend to use POS products endpoint
   - Create usePOS hook
   - Test order creation

3. **Medium Term** (1 day):
   - Add automatic product sync on creation
   - Create bulk sync command
   - Add sync status indicator in UI

4. **Long Term** (1 week):
   - Implement proper service mesh
   - Add product sync queue
   - Add webhook notifications for product changes

## Related Files

- `pos/pos_service/services/inventory_client.py` - Inventory client
- `pos/pos_service/pos/views/pos_views.py` - Order creation
- `qpfrontend/src/modules/pos/modals/OrderModal.tsx` - Frontend modal
- `qpfrontend/src/hooks/useInventory.ts` - Inventory hook
- `qpfrontend/src/services/inventoryService.ts` - Inventory service

## Notes

- The "integrated" endpoints are meant for UI display
- The "query" endpoints are meant for service-to-service calls
- POS should have its own product endpoints that handle this correctly
- Products should be synced across services, not queried on-demand

---

**Status:** Investigation complete, solutions identified  
**Priority:** HIGH - Blocks order creation  
**Recommended:** Solution 1 (Use POS endpoints)
