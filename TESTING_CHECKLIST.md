# POS Order Enhancement - Testing Checklist

## Test Environment Setup

### Prerequisites
- [ ] Database migrations applied: `python manage.py migrate pos`
- [ ] Test data loaded (products, accounts, customers)
- [ ] Accounting service running and accessible
- [ ] Inventory service running and accessible
- [ ] Banking service running and accessible
- [ ] Frontend built and deployed

---

## 1. Backend API Tests

### 1.1 Order Creation - Cash Payment
**Endpoint:** `POST /api/pos/orders/`

**Test Case 1.1.1: Create order with cash payment**
```json
{
  "customer_name": "Test Customer",
  "mark_as_paid": true,
  "payment_account_id": "<cash-account-uuid>",
  "items": [
    {
      "product_id": "<product-uuid>",
      "quantity": 2,
      "unit_price": 25.00
    }
  ],
  "payments": [
    {
      "method": "cash",
      "amount": 50.00,
      "reference": ""
    }
  ]
}
```

**Expected Result:**
- [ ] HTTP 201 Created
- [ ] Order created with state='paid'
- [ ] Payment record created
- [ ] `accounting_sync.success` = true
- [ ] `accounting_sync.invoice_id` is not null
- [ ] `accounting_sync.invoice_number` is not null

**Verification:**
- [ ] Check order in database: `SELECT * FROM pos_order WHERE order_number = 'POS-...'`
- [ ] Check payment in database: `SELECT * FROM pos_payment WHERE order_id = '...'`
- [ ] Check invoice in accounting service
- [ ] Check journal entry in accounting service
- [ ] Check stock level decreased in inventory service

---

### 1.2 Order Creation - Split Payment
**Test Case 1.2.1: Create order with multiple payment methods**
```json
{
  "customer_name": "Test Customer",
  "mark_as_paid": true,
  "payment_account_id": "<bank-account-uuid>",
  "items": [
    {
      "product_id": "<product-uuid>",
      "quantity": 1,
      "unit_price": 100.00
    }
  ],
  "payments": [
    {
      "method": "cash",
      "amount": 60.00,
      "reference": ""
    },
    {
      "method": "card",
      "amount": 40.00,
      "reference": "CARD123456"
    }
  ]
}
```

**Expected Result:**
- [ ] HTTP 201 Created
- [ ] Two payment records created
- [ ] Total paid = 100.00
- [ ] Change = 0.00
- [ ] Accounting sync successful

---

### 1.3 Order Creation - Draft Order
**Test Case 1.3.1: Create draft order (not paid)**
```json
{
  "customer_name": "Test Customer",
  "mark_as_paid": false,
  "items": [
    {
      "product_id": "<product-uuid>",
      "quantity": 1,
      "unit_price": 50.00
    }
  ],
  "notes": "Customer will pay later"
}
```

**Expected Result:**
- [ ] HTTP 201 Created
- [ ] Order created with state='draft'
- [ ] No payment records created
- [ ] No accounting sync attempted
- [ ] Stock NOT deducted

---

### 1.4 Mark Order as Paid
**Endpoint:** `POST /api/pos/orders/<uuid>/mark-as-paid/`

**Test Case 1.4.1: Mark draft order as paid**
```json
{
  "payment_account_id": "<cash-account-uuid>",
  "payments": [
    {
      "method": "cash",
      "amount": 50.00,
      "reference": ""
    }
  ],
  "apply_tax": true
}
```

**Expected Result:**
- [ ] HTTP 200 OK
- [ ] Order state changed to 'paid'
- [ ] Payment record created
- [ ] Accounting sync successful
- [ ] Stock deducted

---

### 1.5 Error Handling Tests

**Test Case 1.5.1: Insufficient stock**
```json
{
  "items": [
    {
      "product_id": "<product-uuid>",
      "quantity": 999999
    }
  ]
}
```
**Expected:** HTTP 400, error message with available quantity

**Test Case 1.5.2: Missing payment account**
```json
{
  "mark_as_paid": true,
  "payment_account_id": "",
  "items": [...]
}
```
**Expected:** HTTP 400, "payment_account_id is required"

**Test Case 1.5.3: Insufficient payment**
```json
{
  "mark_as_paid": true,
  "payment_account_id": "<uuid>",
  "items": [{"product_id": "...", "quantity": 1, "unit_price": 100}],
  "payments": [{"method": "cash", "amount": 50}]
}
```
**Expected:** HTTP 400, "Insufficient payment"

**Test Case 1.5.4: Invalid product ID**
```json
{
  "items": [
    {
      "product_id": "00000000-0000-0000-0000-000000000000",
      "quantity": 1
    }
  ]
}
```
**Expected:** HTTP 404, "Product not found"

**Test Case 1.5.5: Mark already paid order as paid**
```json
POST /api/pos/orders/<paid-order-uuid>/mark-as-paid/
```
**Expected:** HTTP 400, "ORDER_ALREADY_PAID"

---

### 1.6 List Pending Orders
**Endpoint:** `GET /api/pos/orders/pending/`

**Test Case 1.6.1: List all pending orders**
```
GET /api/pos/orders/pending/?limit=50&offset=0
```

**Expected Result:**
- [ ] HTTP 200 OK
- [ ] Returns only orders with state='draft' or state='pending'
- [ ] Includes count, limit, offset
- [ ] Orders sorted by created_at descending

**Test Case 1.6.2: Filter by customer**
```
GET /api/pos/orders/pending/?customer_id=<uuid>
```

**Expected Result:**
- [ ] Returns only orders for specified customer

---

## 2. Frontend Tests

### 2.1 OrderModal Component

**Test Case 2.1.1: Open modal**
- [ ] Modal opens when triggered
- [ ] Form is empty/reset
- [ ] Product dropdown loads
- [ ] Payment account dropdown loads

**Test Case 2.1.2: Add items**
- [ ] Can select product from dropdown
- [ ] Unit price auto-fills from product
- [ ] Total calculates correctly
- [ ] Can add multiple items
- [ ] Can remove items (except last one)

**Test Case 2.1.3: Calculate totals**
- [ ] Subtotal = sum of all item totals
- [ ] Tax checkbox works
- [ ] Tax amount can be entered
- [ ] Discount can be entered
- [ ] Total = subtotal + tax - discount

**Test Case 2.1.4: Payment section**
- [ ] "Mark as Paid" checkbox works
- [ ] Payment section shows/hides correctly
- [ ] Payment account dropdown works
- [ ] Can add multiple payment methods
- [ ] Can remove payment methods (except last one)
- [ ] Payment summary shows correct amounts
- [ ] Change calculation works
- [ ] Remaining balance shows when underpaid

**Test Case 2.1.5: Validation**
- [ ] Error shown if no items
- [ ] Error shown if item has no product
- [ ] Error shown if quantity <= 0
- [ ] Error shown if mark_as_paid but no payment_account
- [ ] Error shown if insufficient payment
- [ ] Error shown if payment method has no amount

**Test Case 2.1.6: Submit**
- [ ] Loading state shows during submission
- [ ] Success: modal closes and list refreshes
- [ ] Error: error message displays
- [ ] Accounting sync status shown in console

---

### 2.2 Payment Account Dropdown

**Test Case 2.2.1: Load payment accounts**
- [ ] Shows bank accounts
- [ ] Shows chart of accounts (ASSET type)
- [ ] Displays correct format: "Bank Name - Account Name"
- [ ] Displays correct format: "Code - Account Name"
- [ ] Shows loading indicator while fetching

**Test Case 2.2.2: Select payment account**
- [ ] Can select bank account
- [ ] Can select chart of account
- [ ] Selected account shows in field
- [ ] Account ID is captured correctly

---

### 2.3 Responsive Design

**Test Case 2.3.1: Desktop (1920x1080)**
- [ ] Modal displays correctly
- [ ] All fields visible
- [ ] Grid layout works
- [ ] Buttons accessible

**Test Case 2.3.2: Tablet (768x1024)**
- [ ] Modal displays correctly
- [ ] Fields stack appropriately
- [ ] Touch targets large enough
- [ ] Scrolling works

**Test Case 2.3.3: Mobile (375x667)**
- [ ] Modal displays correctly
- [ ] All fields accessible
- [ ] Keyboard doesn't obscure fields
- [ ] Can complete full flow

---

## 3. Integration Tests

### 3.1 End-to-End Order Flow

**Test Case 3.1.1: Complete order flow**
1. [ ] Open OrderModal
2. [ ] Add product
3. [ ] Enter customer name
4. [ ] Check "Mark as Paid"
5. [ ] Select payment account
6. [ ] Enter payment amount
7. [ ] Submit order
8. [ ] Verify order appears in list
9. [ ] Verify invoice in accounting
10. [ ] Verify stock decreased

**Test Case 3.1.2: Draft to paid flow**
1. [ ] Create draft order
2. [ ] Find order in pending list
3. [ ] Mark as paid
4. [ ] Verify accounting sync
5. [ ] Verify stock decreased

---

### 3.2 Service Integration

**Test Case 3.2.1: Accounting service down**
- [ ] Order still created
- [ ] accounting_synced = false
- [ ] accounting_sync_error populated
- [ ] Can retry sync later

**Test Case 3.2.2: Inventory service down**
- [ ] Order creation fails gracefully
- [ ] Error message shown
- [ ] No partial data created

**Test Case 3.2.3: Banking service down**
- [ ] Payment accounts don't load
- [ ] Error message shown
- [ ] Can't mark as paid

---

## 4. Database Tests

### 4.1 Data Integrity

**Test Case 4.1.1: Atomic transactions**
- [ ] If accounting sync fails, order still created
- [ ] If payment validation fails, nothing created
- [ ] No orphaned records

**Test Case 4.1.2: Relationships**
- [ ] Order has lines
- [ ] Order has payments
- [ ] Lines reference products
- [ ] Payments reference order

**Test Case 4.1.3: Indexes**
- [ ] Query by corporate_id is fast
- [ ] Query by state is fast
- [ ] Query by accounting_synced is fast

---

## 5. Performance Tests

### 5.1 Load Testing

**Test Case 5.1.1: Create 100 orders**
- [ ] All orders created successfully
- [ ] Response time < 2 seconds per order
- [ ] No database deadlocks
- [ ] No memory leaks

**Test Case 5.1.2: Concurrent orders**
- [ ] 10 simultaneous order creations
- [ ] All succeed
- [ ] No race conditions
- [ ] Stock levels correct

---

## 6. Security Tests

### 6.1 Authorization

**Test Case 6.1.1: Cross-corporate access**
- [ ] User from Corporate A can't access Corporate B orders
- [ ] User from Corporate A can't use Corporate B payment accounts

**Test Case 6.1.2: Permission checks**
- [ ] Only authorized users can create orders
- [ ] Only authorized users can mark as paid
- [ ] Only authorized users can access payment accounts

---

## 7. Accounting Verification

### 7.1 Invoice Creation

**Test Case 7.1.1: Invoice details**
- [ ] Invoice number generated
- [ ] Customer correct
- [ ] Line items match order
- [ ] Amounts correct
- [ ] Tax calculated correctly
- [ ] Status = 'paid'

**Test Case 7.1.2: Journal entry**
- [ ] Debit: Payment account
- [ ] Credit: Revenue account
- [ ] Credit: Tax payable (if tax applied)
- [ ] Amounts balance

---

## 8. Edge Cases

**Test Case 8.1: Zero amount order**
- [ ] Can create order with 100% discount
- [ ] Payment amount = 0
- [ ] Accounting sync works

**Test Case 8.2: Very large order**
- [ ] 100 line items
- [ ] Total > 1,000,000
- [ ] Performance acceptable

**Test Case 8.3: Decimal precision**
- [ ] Quantity with 3 decimals (0.125)
- [ ] Price with 2 decimals (19.99)
- [ ] Totals calculate correctly
- [ ] No rounding errors

**Test Case 8.4: Special characters**
- [ ] Customer name with apostrophe
- [ ] Notes with quotes
- [ ] Reference with special chars
- [ ] No SQL injection

**Test Case 8.5: Walk-in customer**
- [ ] No customer_id provided
- [ ] customer_name = "Walk-in Customer"
- [ ] Accounting sync creates walk-in customer

---

## 9. Regression Tests

**Test Case 9.1: Existing functionality**
- [ ] Can still create orders without payment
- [ ] Can still add/remove lines
- [ ] Can still process returns
- [ ] Sessions still work
- [ ] Loyalty still works

---

## 10. User Acceptance Tests

### 10.1 Cashier Workflow

**Scenario: Cashier sells product for cash**
1. [ ] Cashier opens POS
2. [ ] Scans/selects product
3. [ ] Enters quantity
4. [ ] Checks "Mark as Paid"
5. [ ] Selects cash account
6. [ ] Enters cash amount
7. [ ] Sees change amount
8. [ ] Completes order
9. [ ] Receipt prints (if configured)
10. [ ] Order appears in history

**Acceptance Criteria:**
- [ ] Process takes < 30 seconds
- [ ] No errors
- [ ] Change calculated correctly
- [ ] Receipt shows all details

---

### 10.2 Manager Workflow

**Scenario: Manager reviews pending orders**
1. [ ] Manager opens pending orders
2. [ ] Sees list of unpaid orders
3. [ ] Selects an order
4. [ ] Marks as paid
5. [ ] Enters payment details
6. [ ] Confirms payment
7. [ ] Order moves to paid status

**Acceptance Criteria:**
- [ ] Can filter/search orders
- [ ] Can see order details
- [ ] Can mark multiple orders as paid
- [ ] Accounting sync status visible

---

## Test Results Summary

### Test Execution Date: _______________
### Tester: _______________

| Category | Total Tests | Passed | Failed | Blocked | Pass Rate |
|----------|-------------|--------|--------|---------|-----------|
| Backend API | | | | | |
| Frontend | | | | | |
| Integration | | | | | |
| Database | | | | | |
| Performance | | | | | |
| Security | | | | | |
| Accounting | | | | | |
| Edge Cases | | | | | |
| Regression | | | | | |
| UAT | | | | | |
| **TOTAL** | | | | | |

---

## Critical Bugs Found

| ID | Severity | Description | Status | Fixed By |
|----|----------|-------------|--------|----------|
| | | | | |

---

## Sign-off

### QA Lead
- [ ] All critical tests passed
- [ ] All high-priority bugs fixed
- [ ] Performance acceptable
- [ ] Security verified

**Signature:** _______________ **Date:** _______________

### Technical Lead
- [ ] Code reviewed
- [ ] Architecture approved
- [ ] Documentation complete
- [ ] Ready for deployment

**Signature:** _______________ **Date:** _______________

### Product Owner
- [ ] Features complete
- [ ] User acceptance passed
- [ ] Business requirements met
- [ ] Approved for production

**Signature:** _______________ **Date:** _______________
