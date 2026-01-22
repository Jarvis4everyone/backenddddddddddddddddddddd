# Payment Index Fix - MongoDB Duplicate Key Error

## Problem

When creating payment orders, you were getting this error:

```
pymongo.errors.DuplicateKeyError: E11000 duplicate key error collection: J4E.payments 
index: razorpay_payment_id_1 dup key: { razorpay_payment_id: null }
```

## Root Cause

1. There was a **unique index** on `razorpay_payment_id` field
2. When creating a payment order, `razorpay_payment_id` is `null` (payment hasn't been completed yet)
3. MongoDB unique indexes don't allow multiple `null` values by default
4. When trying to create a second payment order, it failed because there was already a document with `razorpay_payment_id: null`

## Solution

Changed the index to be **sparse**:
- A sparse index only includes documents that have the indexed field
- Multiple `null` values are allowed
- Only non-null values must be unique

## What Changed

In `app/database.py`, the index creation was updated:

**Before:**
```python
await db.database.payments.create_index("razorpay_payment_id", unique=True)
```

**After:**
```python
# Drop old index if exists
try:
    await db.database.payments.drop_index("razorpay_payment_id_1")
except Exception:
    pass

# Create sparse unique index
await db.database.payments.create_index("razorpay_payment_id", unique=True, sparse=True)
```

## How It Works Now

1. **Creating Payment Order**: Multiple payment records can have `razorpay_payment_id: null` ✅
2. **After Payment**: When payment is verified, `razorpay_payment_id` is set to a unique value ✅
3. **Uniqueness**: All non-null `razorpay_payment_id` values are still unique ✅

## Deployment

After deploying this fix:

1. The old index will be automatically dropped on startup
2. A new sparse index will be created
3. Multiple pending payments can now be created without errors

## Manual Fix (If Needed)

If the automatic index drop fails, you can manually fix it in MongoDB:

```javascript
// Connect to MongoDB
use J4E

// Drop the old index
db.payments.dropIndex("razorpay_payment_id_1")

// The new sparse index will be created automatically on next app startup
```

Or using MongoDB Compass or any MongoDB client:
1. Go to `payments` collection
2. Go to Indexes tab
3. Delete the `razorpay_payment_id_1` index
4. Restart the application (it will create the new sparse index)

## Verification

After the fix is deployed:

1. Try creating multiple payment orders - should work without errors
2. Check MongoDB indexes:
   ```javascript
   db.payments.getIndexes()
   ```
   Should see: `{ "razorpay_payment_id": 1 }` with `sparse: true` and `unique: true`

## Related Files

- `app/database.py` - Index creation
- `app/services/payment_service.py` - Payment record creation
- `app/models/payment.py` - Payment model
