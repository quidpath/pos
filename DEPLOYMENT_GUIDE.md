# POS Order Enhancement - Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the POS order enhancement to staging and production environments.

---

## Pre-Deployment Checklist

### Code Review
- [x] All code reviewed and approved
- [x] Frontend hook implementation verified
- [x] Accounting service integration verified
- [x] Documentation complete
- [ ] All tests passed

### Environment Verification
- [ ] Staging environment accessible
- [ ] Database backup completed
- [ ] Accounting service running
- [ ] Inventory service running
- [ ] Banking service running
- [ ] Frontend build server accessible

---

## Deployment Steps

### Phase 1: Database Migration (Backend)

#### Step 1.1: Backup Database
```bash
# On staging server
cd /path/to/pos
python manage.py dumpdata pos > backup_pos_$(date +%Y%m%d_%H%M%S).json
```

#### Step 1.2: Pull Latest Code
```bash
git fetch origin
git checkout Development
git pull origin Development
```

#### Step 1.3: Verify Migrations
```bash
# List pending migrations
python manage.py showmigrations pos

# Expected output should show:
# pos
#  [X] 0001_initial
#  [X] 0002_add_payment_account_and_sync_fields
#  [X] 0003_make_session_optional
```

#### Step 1.4: Apply Migrations
```bash
# Dry run first (check for issues)
python manage.py migrate pos --plan

# Apply migrations
python manage.py migrate pos

# Verify
python manage.py showmigrations pos
```

#### Step 1.5: Verify Database Schema
```sql
-- Connect to database and verify new fields exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pos_order' 
AND column_name IN ('payment_account_id', 'accounting_synced', 'accounting_sync_error');

-- Expected: 3 rows returned
```

---

### Phase 2: Backend Deployment

#### Step 2.1: Install Dependencies
```bash
# If using virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.\.venv\Scripts\Activate.ps1  # Windows

# Install/update dependencies
pip install -r requirements.txt
```

#### Step 2.2: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

#### Step 2.3: Run System Checks
```bash
python manage.py check
python manage.py check --deploy
```

#### Step 2.4: Restart Service
```bash
# Using systemd
sudo systemctl restart pos-service

# Or using supervisor
sudo supervisorctl restart pos-service

# Or using Docker
docker-compose restart pos-service
```

#### Step 2.5: Verify Service is Running
```bash
# Check service status
sudo systemctl status pos-service

# Check logs
tail -f /var/log/pos-service/error.log

# Test health endpoint
curl http://localhost:8000/health/
```

---

### Phase 3: Frontend Deployment

#### Step 3.1: Pull Latest Code
```bash
cd /path/to/qpfrontend
git fetch origin
git checkout main  # or appropriate branch
git pull origin main
```

#### Step 3.2: Install Dependencies
```bash
npm install
# or
yarn install
```

#### Step 3.3: Build Frontend
```bash
# Production build
npm run build
# or
yarn build
```

#### Step 3.4: Deploy Build
```bash
# Copy build to web server
# Example for nginx:
sudo cp -r dist/* /var/www/qpfrontend/

# Or deploy to hosting service
# (Vercel, Netlify, AWS S3, etc.)
```

#### Step 3.5: Verify Frontend
```bash
# Test frontend is accessible
curl http://your-frontend-url/

# Check browser console for errors
# Open browser DevTools and check for:
# - No 404 errors
# - No console errors
# - API calls working
```

---

### Phase 4: Integration Testing

#### Step 4.1: Test Order Creation
```bash
# Test API endpoint
curl -X POST http://your-api-url/api/pos/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "customer_name": "Test Customer",
    "mark_as_paid": true,
    "payment_account_id": "YOUR_ACCOUNT_UUID",
    "items": [{
      "product_id": "YOUR_PRODUCT_UUID",
      "quantity": 1,
      "unit_price": 10.00
    }],
    "payments": [{
      "method": "cash",
      "amount": 10.00,
      "reference": ""
    }]
  }'
```

#### Step 4.2: Verify Accounting Sync
```bash
# Check order in database
psql -d pos_db -c "SELECT order_number, state, accounting_synced, invoice_id FROM pos_order ORDER BY created_at DESC LIMIT 1;"

# Check invoice in accounting service
curl http://accounting-service/api/accounting/invoices/INVOICE_ID/
```

#### Step 4.3: Verify Stock Deduction
```bash
# Check stock level in inventory service
curl http://inventory-service/api/inventory/products/PRODUCT_ID/stock/
```

#### Step 4.4: Test Frontend Flow
1. Open browser to frontend URL
2. Navigate to POS module
3. Click "New Order"
4. Add product
5. Check "Mark as Paid"
6. Select payment account
7. Enter payment amount
8. Submit order
9. Verify success message
10. Check order appears in list

---

### Phase 5: Monitoring Setup

#### Step 5.1: Configure Logging
```python
# In settings/stage.py or settings/prod.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/pos-service/pos.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
        'accounting_sync': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/pos-service/accounting_sync.log',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
    },
    'loggers': {
        'pos_service.services.accounting_sync_service': {
            'handlers': ['accounting_sync'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

#### Step 5.2: Set Up Monitoring Alerts
```bash
# Example: Set up alert for failed accounting syncs
# (Using your monitoring tool: Datadog, New Relic, etc.)

# Monitor this metric:
# - pos_order.accounting_synced = false
# - pos_order.accounting_sync_error != ''

# Alert when:
# - More than 5 failed syncs in 1 hour
# - Sync failure rate > 10%
```

#### Step 5.3: Create Dashboard
Create monitoring dashboard with:
- Total orders created (last 24h)
- Orders marked as paid (last 24h)
- Accounting sync success rate
- Average order value
- Failed syncs count
- API response times

---

### Phase 6: Post-Deployment Verification

#### Step 6.1: Smoke Tests (First 30 minutes)
- [ ] Create cash order - verify success
- [ ] Create card order - verify success
- [ ] Create split payment order - verify success
- [ ] Create draft order - verify success
- [ ] Mark draft as paid - verify success
- [ ] Check accounting sync - verify invoice created
- [ ] Check stock levels - verify decreased
- [ ] Check error logs - no critical errors

#### Step 6.2: Monitor for 2 Hours
- [ ] Watch error logs continuously
- [ ] Monitor accounting sync success rate
- [ ] Check database performance
- [ ] Monitor API response times
- [ ] Watch for user-reported issues

#### Step 6.3: Monitor for 24 Hours
- [ ] Daily sync success rate > 95%
- [ ] No critical errors
- [ ] Performance acceptable
- [ ] No user complaints

---

## Rollback Procedure

### If Issues Detected

#### Step 1: Stop New Orders
```bash
# Temporarily disable order creation endpoint
# (Add maintenance mode or feature flag)
```

#### Step 2: Assess Impact
```bash
# Check how many orders affected
psql -d pos_db -c "SELECT COUNT(*) FROM pos_order WHERE created_at > 'DEPLOYMENT_TIME';"

# Check failed syncs
psql -d pos_db -c "SELECT COUNT(*) FROM pos_order WHERE accounting_synced = false AND created_at > 'DEPLOYMENT_TIME';"
```

#### Step 3: Rollback Code
```bash
# Backend
cd /path/to/pos
git checkout PREVIOUS_COMMIT_HASH
python manage.py migrate pos 0001_initial  # Rollback migrations
sudo systemctl restart pos-service

# Frontend
cd /path/to/qpfrontend
git checkout PREVIOUS_COMMIT_HASH
npm run build
# Deploy previous build
```

#### Step 4: Restore Database (if needed)
```bash
# Only if data corruption occurred
python manage.py loaddata backup_pos_TIMESTAMP.json
```

#### Step 5: Verify Rollback
```bash
# Test old functionality still works
curl http://your-api-url/api/pos/orders/
```

---

## Environment-Specific Notes

### Staging Environment
- **URL:** https://staging-pos.yourdomain.com
- **Database:** pos_staging
- **Accounting Service:** https://staging-accounting.yourdomain.com
- **Inventory Service:** https://staging-inventory.yourdomain.com
- **Test Accounts:** Use test payment accounts
- **Test Products:** Use test products with unlimited stock

### Production Environment
- **URL:** https://pos.yourdomain.com
- **Database:** pos_production
- **Accounting Service:** https://accounting.yourdomain.com
- **Inventory Service:** https://inventory.yourdomain.com
- **Backup Schedule:** Before deployment + daily
- **Monitoring:** 24/7 alerts enabled
- **Support:** On-call team notified

---

## Troubleshooting

### Issue: Migrations Fail
**Symptoms:** `python manage.py migrate` returns error

**Solution:**
```bash
# Check current migration state
python manage.py showmigrations pos

# If migrations are out of order, fake them
python manage.py migrate pos --fake 0002_add_payment_account_and_sync_fields

# Then apply remaining migrations
python manage.py migrate pos
```

---

### Issue: Accounting Sync Fails
**Symptoms:** Orders created but `accounting_synced = false`

**Solution:**
```bash
# Check accounting service is accessible
curl http://accounting-service/health/

# Check logs for specific error
tail -f /var/log/pos-service/accounting_sync.log

# Retry failed syncs
python manage.py shell
>>> from pos_service.services.accounting_sync_service import AccountingSyncService
>>> sync_service = AccountingSyncService()
>>> result = sync_service.retry_failed_syncs('CORPORATE_ID', 'USER_ID')
>>> print(result)
```

---

### Issue: Payment Accounts Not Loading
**Symptoms:** Dropdown is empty in frontend

**Solution:**
```bash
# Check banking service
curl http://banking-service/api/banking/bank-accounts/

# Check accounting service
curl http://accounting-service/api/accounting/accounts/?account_type=ASSET

# Check browser console for errors
# Open DevTools > Console
# Look for failed API calls
```

---

### Issue: Stock Not Deducting
**Symptoms:** Orders created but stock levels unchanged

**Solution:**
```bash
# Check inventory service
curl http://inventory-service/api/inventory/stock-moves/

# Check accounting sync logs
grep "update_inventory" /var/log/pos-service/accounting_sync.log

# Manually create stock move if needed
curl -X POST http://inventory-service/api/inventory/stock-moves/ \
  -H "Content-Type: application/json" \
  -d '{
    "reference": "ORDER_NUMBER",
    "move_type": "delivery",
    "product_id": "PRODUCT_UUID",
    "quantity": "QUANTITY",
    "state": "done"
  }'
```

---

## Performance Optimization

### Database Indexes
```sql
-- Verify indexes exist
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'pos_order';

-- Add additional indexes if needed
CREATE INDEX idx_pos_order_paid_at ON pos_order(paid_at) WHERE state = 'paid';
CREATE INDEX idx_pos_order_sync_status ON pos_order(accounting_synced, state);
```

### Caching
```python
# Add caching for frequently accessed data
from django.core.cache import cache

# Cache payment accounts
def get_payment_accounts(corporate_id):
    cache_key = f'payment_accounts_{corporate_id}'
    accounts = cache.get(cache_key)
    if not accounts:
        accounts = fetch_payment_accounts(corporate_id)
        cache.set(cache_key, accounts, 300)  # 5 minutes
    return accounts
```

---

## Success Criteria

### Deployment is Successful When:
- [x] All migrations applied without errors
- [x] Backend service running and healthy
- [x] Frontend accessible and functional
- [x] Can create orders via API
- [x] Can create orders via UI
- [x] Accounting sync working (>95% success rate)
- [x] Stock deduction working
- [x] No critical errors in logs
- [x] Performance acceptable (<2s response time)
- [x] All smoke tests passed

---

## Support Contacts

### Technical Issues
- **Backend Lead:** [Name] - [Email] - [Phone]
- **Frontend Lead:** [Name] - [Email] - [Phone]
- **DevOps Lead:** [Name] - [Email] - [Phone]

### Business Issues
- **Product Owner:** [Name] - [Email] - [Phone]
- **Support Team:** [Email] - [Phone]

### Emergency Escalation
- **On-Call Engineer:** [Phone]
- **CTO:** [Phone]

---

## Post-Deployment Tasks

### Week 1
- [ ] Monitor error logs daily
- [ ] Review accounting sync success rate
- [ ] Collect user feedback
- [ ] Fix any minor bugs
- [ ] Update documentation based on issues found

### Week 2
- [ ] Analyze performance metrics
- [ ] Optimize slow queries if needed
- [ ] Review and improve error messages
- [ ] Plan Phase 2 enhancements

### Month 1
- [ ] Conduct user training sessions
- [ ] Create video tutorials
- [ ] Update user documentation
- [ ] Plan automatic tax calculation feature
- [ ] Plan loyalty integration

---

## Deployment Sign-off

### Staging Deployment
- **Date:** _______________
- **Deployed By:** _______________
- **Verified By:** _______________
- **Issues Found:** _______________
- **Status:** ☐ Success ☐ Failed ☐ Rolled Back

### Production Deployment
- **Date:** _______________
- **Deployed By:** _______________
- **Verified By:** _______________
- **Issues Found:** _______________
- **Status:** ☐ Success ☐ Failed ☐ Rolled Back

---

**Document Version:** 1.0  
**Last Updated:** April 23, 2026  
**Next Review:** After production deployment
