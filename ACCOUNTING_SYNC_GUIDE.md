# POS to Accounting Automatic Sync Guide

## Overview

POS orders now automatically sync to accounting when marked as paid. This ensures:
- ✅ Revenue is recorded immediately
- ✅ Accounting metrics are always up-to-date  
- ✅ Journal entries are created automatically
- ✅ Tax is properly calculated and recorded (VAT 16%)
- ✅ Inventory is updated (stock moves)
- ✅ CRM is updated (customer LTV and activity)

## New Fields

### POSOrder Model

- **`payment_account_id`** (UUID, nullable): Accounting account where payment was received
- **`accounting_synced`** (Boolean): Whether order has been synced to accounting
- **`accounting_sync_error`** (Text): Error message if sync failed
- **`state`** (Updated): Now includes 'pending' and 'invoiced' states

## Workflows

### Workflow 1: Create Order as Paid (Immediate Sync)

**Use Case**: Customer pays immediately (cash, card, M-Pesa)

**Request**:
```http
POST /api/pos/orders/
Content-Type: application/json

{
  "session": "session-uuid",
  "customer_id": "customer-uuid",  // Optional
  "customer_name": "John Doe",     // Optional
  "mark_as_paid": true,            // Mark as paid immediately
  "payment_account_id": "account-uuid"  // Required if mark_as_paid=true
}
```

**What Happens**:
1. Order is created with `state='paid'`
2. After adding order lines, order is automatically synced to accounting
3. Invoice is created with tax (VAT 16%)
4. Journal entry is posted
5. Inventory is updated (stock moves)
6. CRM is updated (if customer exists)

### Workflow 2: Create Draft Order, Pay Later

**Use Case**: Customer orders now, pays later (credit, layaway)

**Step 1: Create Draft Order**
```http
POST /api/pos/orders/
Content-Type: application/json

{
  "session": "session-uuid",
  "customer_id": "customer-uuid",
  "customer_name": "John Doe"
  // No mark_as_paid flag - defaults to draft
}
```

**Step 2: Add Order Lines**
```http
POST /api/pos/orders/{order_id}/lines/
Content-Type: application/json

{
  "product_id": "product-uuid",
  "quantity": 2,
  "unit_price": "1000.00"
}
```

**Step 3: Mark as Paid When Payment Received**
```http
POST /api/pos/orders/{order_id}/mark-as-paid/
Content-Type: application/json

{
  "payment_account_id": "account-uuid",  // Required
  "payments": [
    {
      "method": "cash",
      "amount": "2000.00",
      "reference": ""
    }
  ],
  "apply_tax": true  // Optional, defaults to true
}
```

**Response**:
```json
{
  "success": true,
  "order": {
    "id": "order-uuid",
    "order_number": "POS-20260422-ABC123",
    "state": "invoiced",
    "accounting_synced": true,
    "invoice_id": "invoice-uuid",
    ...
  },
  "accounting_sync": {
    "success": true,
    "invoice_id": "invoice-uuid",
    "invoice_number": "INV-2026-001",
    "error": null
  }
}
```

### Workflow 3: Process Payment (Existing Orders)

**Use Case**: Draft order ready for payment

**Request**:
```http
POST /api/pos/orders/{order_id}/pay/
Content-Type: application/json

{
  "payment_account_id": "account-uuid",  // Required
  "payments": [
    {
      "method": "cash",
      "amount": "1000.00",
      "reference": ""
    },
    {
      "method": "card",
      "amount": "500.00",
      "reference": "CARD-REF-123"
    }
  ]
}
```

**What Happens**:
1. Payments are recorded
2. Order state changes to 'paid'
3. Automatically syncs to accounting
4. Invoice created with tax
5. Journal entry posted
6. Inventory updated
7. CRM updated

## Endpoints

### List Pending Orders

Get all orders awaiting payment:

```http
GET /api/pos/orders/pending/?limit=50&offset=0
```

**Query Parameters**:
- `limit`: Max results (default: 50)
- `offset`: Pagination offset (default: 0)
- `customer_id`: Filter by customer
- `date_from`: Filter by date (YYYY-MM-DD)
- `date_to`: Filter by date (YYYY-MM-DD)

### Mark Order as Paid

Mark a pending order as paid and sync to accounting:

```http
POST /api/pos/orders/{order_id}/mark-as-paid/
```

**Required Fields**:
- `payment_account_id`: Account where payment was received
- `payments`: Array of payment methods

**Optional Fields**:
- `apply_tax`: Whether to apply tax (default: true)

### Get Invoice Status

Check if order has been synced to accounting:

```http
GET /api/pos/orders/{order_id}/invoice-status/
```

**Response**:
```json
{
  "is_invoiced": true,
  "invoice_id": "invoice-uuid",
  "invoiced_at": "2026-04-22T10:30:00Z",
  "invoiced_by": "user-uuid",
  "invoice_url": "/api/accounting/invoices/{invoice_id}/"
}
```

## Payment Accounts

Payment accounts must be created in the Accounting module first. Common accounts:

- **Cash Account**: For cash payments
- **Bank Account**: For card/bank transfer payments
- **M-Pesa Account**: For M-Pesa payments
- **Petty Cash**: For small cash transactions

**To get available accounts**:
```http
GET /api/accounting/accounts/?type=asset&subtype=cash
```

## Tax Handling

Tax is **automatically applied** when syncing to accounting:

- **Default Tax Rate**: VAT 16% (Kenya)
- **Tax Calculation**: Applied to subtotal after discounts
- **Tax Field**: `order.tax_amount` is updated with calculated tax
- **Invoice**: Tax is included in invoice lines and totals

**To disable tax** (rare cases):
```json
{
  "apply_tax": false
}
```

## Accounting Entries Created

When an order is synced, the following is created:

### 1. Invoice
- **Customer**: From CRM or walk-in customer
- **Lines**: One line per order line
- **Tax**: VAT 16% applied to each line
- **Status**: DRAFT initially, then POSTED
- **Due Date**: Immediate (0 days) since already paid

### 2. Journal Entry (when invoice is posted)
- **Debit**: Cash/Bank Account (payment_account_id)
- **Credit**: Revenue Account
- **Tax**: VAT Payable Account

### 3. Inventory Movements
- **Type**: Delivery (stock out)
- **Quantity**: Order line quantities
- **Reference**: Order number
- **State**: Done (completed)

### 4. CRM Updates
- **Customer LTV**: Increased by order total
- **Activity**: Purchase activity created

## Error Handling

If accounting sync fails:

1. **Order is still marked as paid** - Payment was successful
2. **Error is logged** in `order.accounting_sync_error`
3. **Can be retried** manually or via batch process

**Check sync status**:
```http
GET /api/pos/orders/{order_id}/
```

Look for:
```json
{
  "accounting_synced": false,
  "accounting_sync_error": "Failed to create customer in accounting"
}
```

**Retry sync**:
```http
POST /api/pos/orders/{order_id}/convert-to-invoice/
```

## Migration

### Database Migration

Run the migration to add new fields:

```bash
python manage.py migrate pos
```

This adds:
- `payment_account_id` field
- `accounting_synced` field
- `accounting_sync_error` field
- Updates `state` choices

### Existing Orders

Existing orders are not affected. They can be:
1. Manually converted to invoices using `/convert-to-invoice/` endpoint
2. Left as-is (historical data)

## Frontend Integration

### Order Creation Form

Add fields:
- **Mark as Paid** (checkbox): Enable immediate payment
- **Payment Account** (dropdown): Select account where payment received
  - Only show if "Mark as Paid" is checked
  - Required if "Mark as Paid" is checked

### Payment Processing Form

Add field:
- **Payment Account** (dropdown): Select account where payment received
  - Required field
  - Fetch from `/api/accounting/accounts/?type=asset&subtype=cash`

### Pending Orders List

Show orders with `state='pending'` or `state='draft'`:
- Display order number, customer, amount, date
- Add "Mark as Paid" button
- Opens payment form with payment account dropdown

### Order Detail View

Show accounting sync status:
- **Synced**: Green badge "Synced to Accounting"
- **Not Synced**: Yellow badge "Pending Sync"
- **Error**: Red badge "Sync Failed" with error message
- Show invoice number and link if synced

## Testing

### Test Scenario 1: Immediate Payment

1. Create order with `mark_as_paid=true`
2. Add order lines
3. Verify order state is 'invoiced'
4. Check invoice created in accounting
5. Verify journal entry posted
6. Check inventory updated
7. Verify CRM updated (if customer)

### Test Scenario 2: Deferred Payment

1. Create draft order
2. Add order lines
3. Call `/mark-as-paid/` endpoint
4. Verify same results as Scenario 1

### Test Scenario 3: Error Handling

1. Create order with invalid payment_account_id
2. Verify order is still paid
3. Check error in `accounting_sync_error`
4. Retry with correct account
5. Verify successful sync

## Monitoring

### Check Unsynced Orders

```http
GET /api/pos/orders/?state=paid&accounting_synced=false
```

### Batch Retry Failed Syncs

Create a scheduled task to retry failed syncs:

```python
from pos_service.services.accounting_sync_service import AccountingSyncService

sync_service = AccountingSyncService()
result = sync_service.retry_failed_syncs(
    corporate_id='corporate-uuid',
    user_id='system-user-uuid',
    limit=50
)

print(f"Retried {result['total']} orders")
print(f"Success: {result['success']}")
print(f"Failed: {result['failed']}")
```

## Benefits

1. **Real-time Accounting**: Revenue recorded immediately when payment received
2. **Accurate Metrics**: Dashboard shows up-to-date revenue, receivables, etc.
3. **Audit Trail**: Complete trail from order → invoice → journal entry
4. **Tax Compliance**: Automatic VAT calculation and recording
5. **Inventory Accuracy**: Stock levels updated in real-time
6. **Customer Insights**: CRM tracks purchase history and LTV
7. **Reduced Manual Work**: No need to manually create invoices
8. **Error Recovery**: Failed syncs can be retried without data loss

## Support

For issues or questions:
1. Check `accounting_sync_error` field for error details
2. Verify payment account exists and is active
3. Check accounting service is online
4. Review logs for detailed error messages
5. Retry sync using `/convert-to-invoice/` endpoint
