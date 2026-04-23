# POS Order Enhancement Guide

## Overview

The POS order creation system has been enhanced to include comprehensive payment recording and automatic accounting synchronization. This ensures that all sales transactions are properly tracked and integrated with the accounting system for accurate financial monitoring.

## Key Enhancements

### 1. Payment Recording
- **Multiple Payment Methods**: Support for cash, card, M-Pesa, bank transfer, and other payment methods
- **Split Payments**: Ability to accept multiple payment methods for a single order
- **Payment Account Selection**: Choose which account (bank account or chart of accounts) receives the payment
- **Payment References**: Track transaction references for each payment method

### 2. Accounting Integration
- **Automatic Sync**: Orders marked as paid are automatically synced to the accounting system
- **Invoice Creation**: Generates invoices in the accounting module
- **Journal Entries**: Creates proper double-entry bookkeeping records
- **Account Mapping**: Maps POS payments to appropriate accounting accounts

### 3. Enhanced Order Flow
- **Draft Orders**: Save orders as drafts for later completion
- **Immediate Payment**: Mark orders as paid during creation
- **Inventory Validation**: Real-time stock checking during order creation
- **Customer Tracking**: Optional customer information for loyalty and reporting

## Frontend Changes

### OrderModal Component (`qpfrontend/src/modules/pos/modals/OrderModal.tsx`)

#### New Features:
1. **Payment Section**: 
   - Checkbox to mark order as paid
   - Payment account selection (bank accounts + chart of accounts)
   - Multiple payment methods with amounts and references
   - Real-time payment validation and change calculation

2. **Enhanced Validation**:
   - Validates payment amounts match order total
   - Ensures payment account is selected when marking as paid
   - Checks all payment methods have valid amounts

3. **Improved UX**:
   - Visual payment summary with remaining balance
   - Change calculation for overpayments
   - Clear error messages for payment issues

#### New Hooks:
- `useBanking.ts`: Provides unified access to bank accounts and chart of accounts
- `usePaymentAccounts()`: Returns combined list of payment accounts with proper formatting

### API Integration

#### Enhanced Order Creation:
```typescript
const orderData = {
  customer_name: 'Walk-in Customer',
  mark_as_paid: true,
  payment_account_id: 'account-uuid',
  notes: 'Order notes',
  items: [
    {
      product_id: 'product-uuid',
      quantity: 2,
      unit_price: 25.00,
      discount_percent: 0
    }
  ],
  payments: [
    {
      method: 'cash',
      amount: 40.00,
      reference: ''
    },
    {
      method: 'card',
      amount: 10.00,
      reference: 'TXN123456'
    }
  ]
};
```

## Backend Changes

### Enhanced Order Creation (`pos/pos_service/pos/views/pos_views.py`)

#### New `create_complete_order` Function:
- Creates order, lines, and payments in a single atomic transaction
- Validates inventory availability for all items
- Processes multiple payment methods
- Automatically syncs to accounting when marked as paid
- Returns accounting sync status in response

#### Key Features:
1. **Atomic Transactions**: All operations wrapped in database transaction
2. **Inventory Validation**: Checks stock levels before creating order lines
3. **Payment Processing**: Handles multiple payment methods with validation
4. **Accounting Sync**: Automatic integration with accounting system
5. **Error Handling**: Comprehensive error messages and rollback on failure

### Model Enhancements (`pos/pos_service/pos/models/order.py`)

#### New `calculate_totals` Method:
```python
def calculate_totals(self):
    """Calculate and update order totals based on order lines"""
    lines = self.lines.all()
    subtotal = sum(line.subtotal for line in lines)
    self.subtotal = subtotal
    self.total_amount = subtotal - self.discount_amount + self.tax_amount
    
    # Update line subtotals with discounts
    for line in lines:
        line.discount_amount = (line.unit_price * line.quantity * line.discount_percent) / 100
        line.subtotal = (line.unit_price * line.quantity) - line.discount_amount
        line.save()
    
    self.save()
```

## Accounting Synchronization

### Automatic Sync Process:
1. **Customer Creation**: Creates or retrieves customer in accounting system
2. **Invoice Generation**: Creates invoice with order details
3. **Journal Entry**: Posts double-entry bookkeeping records
4. **Payment Recording**: Records payment against invoice
5. **Inventory Update**: Creates stock movements for delivered items
6. **CRM Update**: Updates customer lifetime value and activity

### Sync Response:
```json
{
  "accounting_sync": {
    "success": true,
    "invoice_id": "invoice-uuid",
    "invoice_number": "INV-20240423-001",
    "error": null
  }
}
```

## Database Schema

### POSOrder Fields:
- `payment_account_id`: UUID reference to accounting account
- `accounting_synced`: Boolean flag for sync status
- `accounting_sync_error`: Error message if sync fails
- `invoice_id`: Reference to created invoice
- `is_invoiced`: Boolean flag for invoice creation
- `notes`: Order notes/comments

### POSPayment Fields:
- `method`: Payment method (cash, card, mpesa, bank, loyalty, other)
- `amount`: Payment amount
- `reference`: Transaction reference
- `state`: Payment state (pending, completed, failed, cancelled)

## Usage Examples

### Creating a Cash Order:
```typescript
const cashOrder = {
  customer_name: 'John Doe',
  mark_as_paid: true,
  payment_account_id: 'cash-account-uuid',
  items: [{ product_id: 'prod-1', quantity: 1, unit_price: 50.00 }],
  payments: [{ method: 'cash', amount: 50.00, reference: '' }]
};
```

### Creating a Split Payment Order:
```typescript
const splitOrder = {
  customer_name: 'Jane Smith',
  mark_as_paid: true,
  payment_account_id: 'bank-account-uuid',
  items: [{ product_id: 'prod-1', quantity: 2, unit_price: 30.00 }],
  payments: [
    { method: 'cash', amount: 40.00, reference: '' },
    { method: 'card', amount: 20.00, reference: 'CARD123' }
  ]
};
```

### Creating a Draft Order:
```typescript
const draftOrder = {
  customer_name: 'Bob Wilson',
  mark_as_paid: false,
  items: [{ product_id: 'prod-1', quantity: 1, unit_price: 25.00 }],
  notes: 'Customer will pay later'
};
```

## Error Handling

### Common Errors:
1. **Insufficient Stock**: Returns available quantity and requested quantity
2. **Invalid Payment**: Payment amount doesn't match order total
3. **Missing Payment Account**: Required when marking as paid
4. **Product Not Found**: Invalid product ID in inventory
5. **Accounting Sync Failure**: Order created but sync failed (can be retried)

### Error Response Format:
```json
{
  "error": "Insufficient stock for Product Name",
  "available": "5",
  "requested": "10"
}
```

## Benefits

### For Users:
1. **Complete Transaction Flow**: Handle entire sale process in one interface
2. **Real-time Validation**: Immediate feedback on stock and payment issues
3. **Flexible Payments**: Support for multiple payment methods
4. **Automatic Accounting**: No manual data entry required

### For Business:
1. **Accurate Records**: All transactions properly recorded in accounting
2. **Real-time Reporting**: Immediate financial data availability
3. **Inventory Tracking**: Automatic stock level updates
4. **Audit Trail**: Complete transaction history with payment details

### For Developers:
1. **Atomic Operations**: Data consistency guaranteed
2. **Error Recovery**: Comprehensive error handling and rollback
3. **Extensible Design**: Easy to add new payment methods or features
4. **API Consistency**: Unified interface for order operations

## Future Enhancements

### Planned Features:
1. **Tax Calculations**: Automatic tax computation based on products and customer location
2. **Loyalty Integration**: Points earning and redemption during order creation
3. **Promotions**: Automatic discount application based on rules
4. **Receipt Generation**: PDF receipt creation and email delivery
5. **Return Processing**: Handle returns and refunds with accounting integration
6. **Offline Support**: Local storage for orders when network is unavailable

### Technical Improvements:
1. **Caching**: Cache frequently accessed data (products, accounts)
2. **Batch Processing**: Handle multiple orders efficiently
3. **Webhook Integration**: Real-time notifications for external systems
4. **Advanced Reporting**: Detailed sales analytics and insights
5. **Mobile Optimization**: Touch-friendly interface for tablets

## Conclusion

The enhanced POS order system provides a complete, integrated solution for point-of-sale operations with automatic accounting synchronization. This ensures accurate financial records, reduces manual data entry, and provides real-time business insights while maintaining data consistency and audit trails.