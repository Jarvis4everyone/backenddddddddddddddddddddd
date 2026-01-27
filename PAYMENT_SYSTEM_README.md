# Payment System Documentation - Jarvis4Everyone

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Payment Flow](#payment-flow)
4. [API Routes](#api-routes)
5. [Schemas & Models](#schemas--models)
6. [Services](#services)
7. [Razorpay Integration](#razorpay-integration)
8. [Database Structure](#database-structure)
9. [Security](#security)
10. [Error Handling](#error-handling)
11. [Testing](#testing)
12. [Deployment](#deployment)

---

## Overview

The payment system integrates with **Razorpay** to handle subscription payments for Jarvis4Everyone. It manages the complete payment lifecycle from order creation to subscription activation.

### Key Features

- ✅ Razorpay payment gateway integration
- ✅ Payment order creation and verification
- ✅ Automatic subscription activation on successful payment
- ✅ Webhook support for payment status updates
- ✅ Payment record tracking in MongoDB
- ✅ Signature verification for security
- ✅ Support for multiple payment statuses (pending, completed, failed, refunded)

### Technology Stack

- **Backend Framework**: FastAPI (Python)
- **Payment Gateway**: Razorpay
- **Database**: MongoDB
- **Authentication**: JWT tokens
- **Validation**: Pydantic models

---

## Architecture

### System Components

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │
       │ 1. Create Order Request
       ▼
┌─────────────────────────────────┐
│   FastAPI Backend               │
│                                 │
│  ┌──────────────────────────┐  │
│  │  Payment Router          │  │
│  │  /payments/create-order  │  │
│  └───────────┬──────────────┘  │
│              │                  │
│  ┌───────────▼──────────────┐  │
│  │  PaymentService          │  │
│  │  - create_order()        │  │
│  │  - create_payment_record()│  │
│  └───────────┬──────────────┘  │
│              │                  │
└──────────────┼──────────────────┘
               │
               │ 2. Create Razorpay Order
               ▼
        ┌──────────────┐
        │   Razorpay   │
        │   API        │
        └──────┬───────┘
               │
               │ 3. Return Order ID
               ▼
        ┌──────────────┐
        │   MongoDB    │
        │   Payments   │
        │   Collection │
        └──────────────┘
```

### Payment Flow Architecture

```
User → Frontend → Backend → Razorpay → User Payment → Razorpay → Backend → Subscription Activated
```

---

## Payment Flow

### Complete Payment Journey

```
1. User clicks "Subscribe"
   ↓
2. Frontend calls POST /payments/create-order
   ↓
3. Backend creates Razorpay order
   ↓
4. Backend saves payment record (status: pending)
   ↓
5. Frontend initializes Razorpay checkout
   ↓
6. User completes payment on Razorpay
   ↓
7. Razorpay returns payment details
   ↓
8. Frontend calls POST /payments/verify
   ↓
9. Backend verifies payment signature
   ↓
10. Backend updates payment status (status: completed)
   ↓
11. Backend activates subscription (1 month)
   ↓
12. User gets access to premium features
```

### Alternative Flow (Webhook)

```
1-6. Same as above
   ↓
7. Razorpay sends webhook to POST /payments/webhook
   ↓
8. Backend verifies webhook signature
   ↓
9. Backend updates payment status
   ↓
10. Backend activates subscription
```

---

## API Routes

### Route 1: Create Payment Order

**Endpoint**: `POST /payments/create-order`

**Authentication**: Required (Bearer token)

**Location**: `app/routers/payment.py`

#### Code Implementation

```python
@router.post("/create-order", response_model=dict)
async def create_payment_order(
    payment_data: PaymentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create Razorpay order for payment"""
    # Create Razorpay order
    order = await PaymentService.create_order(payment_data.amount, payment_data.currency)
    
    # Create payment record
    payment = await PaymentService.create_payment_record(
        current_user["id"],
        current_user["email"],
        payment_data.amount,
        payment_data.currency,
        order["id"]
    )
    
    return {
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "key_id": settings.razorpay_key_id,
        "payment_id": payment["id"]
    }
```

#### Request Schema

```python
class PaymentCreate(BaseModel):
    amount: float      # Amount in rupees (e.g., 299.00)
    currency: str = "INR"
```

#### Request Example

```json
{
  "amount": 299.00,
  "currency": "INR"
}
```

#### Response Schema

```json
{
  "order_id": "order_ABC123XYZ",
  "amount": 29900,           // Amount in paise
  "currency": "INR",
  "key_id": "rzp_test_xxxxx",
  "payment_id": "507f1f77bcf86cd799439013"
}
```

#### Process Flow

1. **Validate Request**: Pydantic validates `PaymentCreate` schema
2. **Authenticate User**: `get_current_user` dependency verifies JWT token
3. **Create Razorpay Order**: 
   - Converts amount from rupees to paise (multiply by 100)
   - Calls Razorpay API: `razorpay_client.order.create()`
   - Returns order with `order_id`
4. **Create Payment Record**: 
   - Saves payment to MongoDB with status "pending"
   - Stores user_id, email, amount, currency, razorpay_order_id
5. **Return Response**: 
   - Returns order_id, amount (in paise), currency, key_id, payment_id
   - Frontend uses these to initialize Razorpay checkout

#### Error Handling

- **401 Unauthorized**: Invalid or missing JWT token
- **400 Bad Request**: Invalid request body (Pydantic validation)
- **500 Internal Server Error**: Razorpay API failure or database error

---

### Route 2: Verify Payment

**Endpoint**: `POST /payments/verify`

**Authentication**: Required (Bearer token)

**Location**: `app/routers/payment.py`

#### Code Implementation

```python
@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    verify_data: PaymentVerify,
    current_user: dict = Depends(get_current_user)
):
    """Verify Razorpay payment and activate subscription"""
    # Get payment record
    payment = await PaymentService.get_payment_by_order_id(verify_data.razorpay_order_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found"
        )
    
    # Verify payment belongs to current user
    if payment.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Payment does not belong to current user"
        )
    
    # Verify payment signature
    is_valid = await PaymentService.verify_payment(
        verify_data.razorpay_order_id,
        verify_data.razorpay_payment_id,
        verify_data.razorpay_signature
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )
    
    # Update payment status
    payment = await PaymentService.update_payment_status(
        verify_data.razorpay_order_id,
        verify_data.razorpay_payment_id,
        verify_data.razorpay_signature,
        "completed"
    )
    
    # Activate subscription (1 month for now)
    await SubscriptionService.renew_subscription(current_user["id"], 1)
    
    return payment
```

#### Request Schema

```python
class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
```

#### Request Example

```json
{
  "razorpay_order_id": "order_ABC123XYZ",
  "razorpay_payment_id": "pay_DEF456UVW",
  "razorpay_signature": "signature_GHI789RST"
}
```

#### Response Schema

```python
class PaymentResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    email: str
    plan_id: str
    amount: float
    currency: str
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    status: Literal["pending", "completed", "failed", "refunded"]
    created_at: datetime
```

#### Process Flow

1. **Validate Request**: Pydantic validates `PaymentVerify` schema
2. **Authenticate User**: Verify JWT token
3. **Find Payment Record**: Query MongoDB by `razorpay_order_id`
4. **Verify Ownership**: Ensure payment belongs to current user
5. **Verify Signature**: 
   - Use Razorpay utility to verify payment signature
   - Prevents tampering and ensures payment authenticity
6. **Update Payment Status**: 
   - Update payment record with payment_id, signature, status="completed"
7. **Activate Subscription**: 
   - Call `SubscriptionService.renew_subscription(user_id, 1)`
   - Creates new subscription or renews existing one
   - Sets status to "active" and calculates end_date (1 month from now)
8. **Return Payment**: Return updated payment record

#### Security Checks

- ✅ User authentication required
- ✅ Payment ownership verification
- ✅ Razorpay signature verification
- ✅ Payment record existence check

#### Error Handling

- **404 Not Found**: Payment record not found
- **403 Forbidden**: Payment doesn't belong to current user
- **400 Bad Request**: Invalid payment signature
- **401 Unauthorized**: Invalid or missing JWT token

---

### Route 3: Razorpay Webhook

**Endpoint**: `POST /payments/webhook`

**Authentication**: Not required (uses signature verification)

**Location**: `app/routers/payment.py`

#### Code Implementation

```python
@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Handle Razorpay webhook (for payment status updates)"""
    # Get webhook signature from headers
    signature = request.headers.get("X-Razorpay-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing webhook signature"
        )
    
    # Get request body
    body = await request.body()
    body_str = body.decode("utf-8")
    
    # Verify webhook signature
    is_valid = await PaymentService.verify_webhook_signature(body_str, signature)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    # Parse webhook payload
    try:
        payload = json.loads(body_str)
        event = payload.get("event")
        
        if event == "payment.captured":
            # Payment successful
            payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_data.get("order_id")
            
            if order_id:
                payment = await PaymentService.get_payment_by_order_id(order_id)
                if payment and payment["status"] == "pending":
                    await PaymentService.update_payment_status(
                        order_id,
                        payment_data.get("id", ""),
                        signature,
                        "completed"
                    )
                    
                    # Activate subscription if user exists
                    if payment.get("user_id"):
                        await SubscriptionService.renew_subscription(str(payment["user_id"]), 1)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"[bold red]✗[/bold red] Webhook processing error: [red]{str(e)}[/red]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )
```

#### Webhook Payload Structure

```json
{
  "event": "payment.captured",
  "payload": {
    "payment": {
      "entity": {
        "id": "pay_DEF456UVW",
        "order_id": "order_ABC123XYZ",
        "amount": 29900,
        "currency": "INR",
        "status": "captured",
        ...
      }
    }
  }
}
```

#### Process Flow

1. **Extract Signature**: Get `X-Razorpay-Signature` from request headers
2. **Get Request Body**: Read raw request body as string
3. **Verify Signature**: 
   - Use Razorpay utility with webhook secret
   - Ensures webhook is from Razorpay
4. **Parse Payload**: Parse JSON payload
5. **Handle Event**: 
   - Check if event is `payment.captured`
   - Extract payment details from payload
6. **Update Payment**: 
   - Find payment by order_id
   - Update status to "completed" if still "pending"
7. **Activate Subscription**: 
   - Renew subscription for the user
   - Grant 1 month access

#### Security

- ✅ Webhook signature verification (prevents spoofing)
- ✅ Idempotent processing (only processes if status is "pending")
- ✅ Error logging for debugging

#### Error Handling

- **400 Bad Request**: Missing or invalid webhook signature
- **500 Internal Server Error**: Error processing webhook payload

---

## Schemas & Models

### Request Schemas

#### PaymentCreate

**Location**: `app/schemas/payment.py`

```python
class PaymentCreate(BaseModel):
    amount: float          # Amount in rupees (e.g., 299.00)
    currency: str = "INR"  # Currency code, defaults to INR
```

**Validation**:
- `amount`: Must be a positive float
- `currency`: String, defaults to "INR"

**Example**:
```json
{
  "amount": 299.00,
  "currency": "INR"
}
```

#### PaymentVerify

**Location**: `app/schemas/payment.py`

```python
class PaymentVerify(BaseModel):
    razorpay_order_id: str    # Order ID from Razorpay
    razorpay_payment_id: str  # Payment ID from Razorpay
    razorpay_signature: str   # Payment signature from Razorpay
```

**Validation**:
- All fields are required strings
- No default values

**Example**:
```json
{
  "razorpay_order_id": "order_ABC123XYZ",
  "razorpay_payment_id": "pay_DEF456UVW",
  "razorpay_signature": "signature_GHI789RST"
}
```

### Response Schemas

#### PaymentResponse

**Location**: `app/schemas/payment.py`

```python
class PaymentResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    email: str
    plan_id: str
    amount: float
    currency: str
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    status: Literal["pending", "completed", "failed", "refunded"]
    created_at: datetime
```

**Fields**:
- `id`: Payment record ID (MongoDB ObjectId as string)
- `user_id`: User who made the payment (optional, in case user is deleted)
- `email`: User email at time of payment (snapshot)
- `plan_id`: Subscription plan ID (currently "monthly")
- `amount`: Payment amount in rupees
- `currency`: Currency code (INR)
- `razorpay_order_id`: Razorpay order ID
- `razorpay_payment_id`: Razorpay payment ID (null until payment completed)
- `status`: Payment status
- `created_at`: Payment creation timestamp

**Example**:
```json
{
  "id": "507f1f77bcf86cd799439013",
  "user_id": "507f1f77bcf86cd799439011",
  "email": "john@example.com",
  "plan_id": "monthly",
  "amount": 299.00,
  "currency": "INR",
  "razorpay_order_id": "order_ABC123XYZ",
  "razorpay_payment_id": "pay_DEF456UVW",
  "status": "completed",
  "created_at": "2024-01-15T10:35:00Z"
}
```

### Database Models

#### Payment Model

**Location**: `app/models/payment.py`

```python
class Payment(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: Optional[PyObjectId] = None
    email: EmailStr
    plan_id: str = "monthly"
    amount: float
    currency: str = "INR"
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    status: Literal["pending", "completed", "failed", "refunded"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Database Indexes**:
- `user_id`: Index for user queries
- `razorpay_order_id`: Unique index
- `razorpay_payment_id`: Sparse unique index (allows multiple nulls)
- `email`: Index for email queries
- `created_at`: Index for sorting

---

## Services

### PaymentService

**Location**: `app/services/payment_service.py`

#### Methods

##### 1. create_order()

```python
@staticmethod
async def create_order(amount: float, currency: str = "INR") -> dict:
    """Create Razorpay order"""
    order_data = {
        "amount": int(amount * 100),  # Convert to paise
        "currency": currency,
        "payment_capture": 1
    }
    order = razorpay_client.order.create(data=order_data)
    return order
```

**Parameters**:
- `amount`: Amount in rupees (float)
- `currency`: Currency code (default: "INR")

**Process**:
1. Converts amount from rupees to paise (multiply by 100)
2. Creates Razorpay order with `payment_capture: 1` (auto-capture)
3. Returns Razorpay order object

**Returns**: Razorpay order dict with `id`, `amount`, `currency`, etc.

##### 2. create_payment_record()

```python
@staticmethod
async def create_payment_record(
    user_id: str, 
    email: str, 
    amount: float, 
    currency: str, 
    razorpay_order_id: str
) -> dict:
    """Create payment record in database"""
    payment = {
        "user_id": ObjectId(user_id),
        "email": email,
        "plan_id": "monthly",
        "amount": amount,
        "currency": currency,
        "razorpay_order_id": razorpay_order_id,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    result = await db.database.payments.insert_one(payment)
    payment = await db.database.payments.find_one({"_id": result.inserted_id})
    payment["id"] = str(payment["_id"])
    if payment.get("user_id"):
        payment["user_id"] = str(payment["user_id"])
    return payment
```

**Parameters**:
- `user_id`: User ID (string, converted to ObjectId)
- `email`: User email (snapshot at payment time)
- `amount`: Payment amount in rupees
- `currency`: Currency code
- `razorpay_order_id`: Order ID from Razorpay

**Process**:
1. Creates payment document with status "pending"
2. Inserts into MongoDB `payments` collection
3. Retrieves inserted document
4. Converts ObjectId to string for JSON serialization
5. Returns payment dict

##### 3. verify_payment()

```python
@staticmethod
async def verify_payment(
    razorpay_order_id: str, 
    razorpay_payment_id: str, 
    razorpay_signature: str
) -> bool:
    """Verify Razorpay payment signature"""
    try:
        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        }
        razorpay_client.utility.verify_payment_signature(params_dict)
        return True
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        return False
```

**Parameters**:
- `razorpay_order_id`: Order ID
- `razorpay_payment_id`: Payment ID
- `razorpay_signature`: Payment signature

**Process**:
1. Creates params dict with all three fields
2. Uses Razorpay utility to verify signature
3. Returns True if valid, False if invalid

**Security**: Prevents payment tampering and ensures authenticity

##### 4. update_payment_status()

```python
@staticmethod
async def update_payment_status(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    status: str
) -> Optional[dict]:
    """Update payment status after verification"""
    payment = await db.database.payments.find_one({"razorpay_order_id": razorpay_order_id})
    if not payment:
        return None
    
    update_data = {
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
        "status": status
    }
    
    await db.database.payments.update_one(
        {"_id": payment["_id"]},
        {"$set": update_data}
    )
    
    payment = await db.database.payments.find_one({"_id": payment["_id"]})
    payment["id"] = str(payment["_id"])
    if payment.get("user_id"):
        payment["user_id"] = str(payment["user_id"])
    return payment
```

**Parameters**:
- `razorpay_order_id`: Order ID to find payment
- `razorpay_payment_id`: Payment ID to store
- `razorpay_signature`: Signature to store
- `status`: New status ("completed", "failed", etc.)

**Process**:
1. Finds payment by order_id
2. Updates payment with payment_id, signature, and status
3. Retrieves updated payment
4. Converts ObjectId to string
5. Returns updated payment

##### 5. get_payment_by_order_id()

```python
@staticmethod
async def get_payment_by_order_id(razorpay_order_id: str) -> Optional[dict]:
    """Get payment by Razorpay order ID"""
    payment = await db.database.payments.find_one({"razorpay_order_id": razorpay_order_id})
    if payment:
        payment["id"] = str(payment["_id"])
        if payment.get("user_id"):
            payment["user_id"] = str(payment["user_id"])
    return payment
```

**Parameters**:
- `razorpay_order_id`: Order ID to search

**Returns**: Payment dict or None if not found

##### 6. verify_webhook_signature()

```python
@staticmethod
async def verify_webhook_signature(payload: str, signature: str) -> bool:
    """Verify Razorpay webhook signature"""
    try:
        razorpay_client.utility.verify_webhook_signature(
            payload, 
            signature, 
            settings.razorpay_webhook_secret
        )
        return True
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        return False
```

**Parameters**:
- `payload`: Raw request body as string
- `signature`: Webhook signature from headers

**Process**:
1. Uses Razorpay utility with webhook secret
2. Verifies signature matches payload
3. Returns True if valid

**Security**: Ensures webhook is from Razorpay, not spoofed

---

## Razorpay Integration

### Configuration

**Location**: `app/config.py`

```python
class Settings(BaseSettings):
    razorpay_key_id: str
    razorpay_key_secret: str
    razorpay_webhook_secret: str
```

**Environment Variables**:
```env
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_secret_key
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
```

### Client Initialization

**Location**: `app/services/payment_service.py`

```python
import razorpay
from app.config import settings

razorpay_client = razorpay.Client(
    auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
)
```

### Amount Conversion

Razorpay requires amounts in **paise** (smallest currency unit):

```python
# Input: 299.00 (rupees)
# Output: 29900 (paise)
amount_in_paise = int(amount * 100)
```

### Payment Capture

Orders are created with `payment_capture: 1` for automatic capture:

```python
order_data = {
    "amount": int(amount * 100),
    "currency": currency,
    "payment_capture": 1  # Auto-capture payment
}
```

### Signature Verification

#### Payment Signature

```python
params_dict = {
    "razorpay_order_id": order_id,
    "razorpay_payment_id": payment_id,
    "razorpay_signature": signature
}
razorpay_client.utility.verify_payment_signature(params_dict)
```

#### Webhook Signature

```python
razorpay_client.utility.verify_webhook_signature(
    payload,      # Raw request body
    signature,    # X-Razorpay-Signature header
    webhook_secret
)
```

### Webhook Setup

1. **Razorpay Dashboard**:
   - Go to Settings → Webhooks
   - Add webhook URL: `https://your-backend.com/payments/webhook`
   - Select events: `payment.captured`
   - Copy webhook secret

2. **Backend Configuration**:
   - Set `RAZORPAY_WEBHOOK_SECRET` in environment variables
   - Webhook endpoint is public (no auth, uses signature verification)

---

## Database Structure

### Payments Collection

**Collection Name**: `payments`

**Schema**:
```javascript
{
  "_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "email": "user@example.com",
  "plan_id": "monthly",
  "amount": 299.00,
  "currency": "INR",
  "razorpay_order_id": "order_ABC123XYZ",
  "razorpay_payment_id": "pay_DEF456UVW",  // null until payment completed
  "razorpay_signature": "signature_...",    // null until payment completed
  "status": "pending" | "completed" | "failed" | "refunded",
  "created_at": ISODate("2024-01-15T10:35:00Z")
}
```

### Indexes

**Location**: `app/database.py`

```python
# User index
await db.database.payments.create_index("user_id")

# Unique order ID index
await db.database.payments.create_index("razorpay_order_id", unique=True)

# Sparse unique payment ID index (allows multiple nulls)
await db.database.payments.create_index("razorpay_payment_id", unique=True, sparse=True)

# Email index
await db.database.payments.create_index("email")

# Created at index (for sorting)
await db.database.payments.create_index("created_at")
```

**Why Sparse Index?**
- `razorpay_payment_id` is `null` when payment is created
- Multiple pending payments can have `null` values
- Sparse index only indexes non-null values
- Allows multiple `null` values while maintaining uniqueness for non-null values

---

## Security

### Authentication

- All payment routes (except webhook) require JWT authentication
- Token verified via `get_current_user` dependency
- User must be logged in to create orders or verify payments

### Authorization

- Payment verification checks ownership:
  ```python
  if payment.get("user_id") != current_user["id"]:
      raise HTTPException(status_code=403, detail="Payment does not belong to current user")
  ```

### Signature Verification

- **Payment Signature**: Verifies payment authenticity from Razorpay
- **Webhook Signature**: Verifies webhook is from Razorpay (not spoofed)

### Data Validation

- Pydantic schemas validate all request data
- Type checking and constraint validation
- Prevents invalid data from reaching business logic

### Secure Storage

- Payment records store user email snapshot (in case user is deleted)
- Sensitive data (signatures) stored securely in MongoDB
- No sensitive data in logs

---

## Error Handling

### Error Types

#### 1. Authentication Errors

```python
HTTPException(status_code=401, detail="Unauthorized")
```

**Causes**:
- Missing JWT token
- Invalid/expired token
- Malformed token

#### 2. Validation Errors

```python
HTTPException(status_code=400, detail="Validation error")
```

**Causes**:
- Invalid request body
- Missing required fields
- Invalid data types

#### 3. Not Found Errors

```python
HTTPException(status_code=404, detail="Payment record not found")
```

**Causes**:
- Payment order_id doesn't exist
- Payment was deleted

#### 4. Forbidden Errors

```python
HTTPException(status_code=403, detail="Payment does not belong to current user")
```

**Causes**:
- User trying to verify someone else's payment

#### 5. Signature Verification Errors

```python
HTTPException(status_code=400, detail="Invalid payment signature")
```

**Causes**:
- Tampered payment data
- Invalid signature from Razorpay
- Wrong order_id/payment_id combination

#### 6. Server Errors

```python
HTTPException(status_code=500, detail="Internal server error")
```

**Causes**:
- Razorpay API failure
- Database connection issues
- Unexpected exceptions

### Error Logging

All errors are logged with context:

```python
logger.error(f"Payment verification failed for order {order_id}: {str(e)}")
```

---

## Testing

### Manual Testing

#### 1. Create Payment Order

```bash
curl -X POST https://backend-gchd.onrender.com/payments/create-order \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 299.00,
    "currency": "INR"
  }'
```

#### 2. Verify Payment

```bash
curl -X POST https://backend-gchd.onrender.com/payments/verify \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "razorpay_order_id": "order_ABC123",
    "razorpay_payment_id": "pay_DEF456",
    "razorpay_signature": "signature_GHI789"
  }'
```

### Test Scenarios

1. **Happy Path**:
   - Create order → Complete payment → Verify → Subscription activated

2. **Invalid Signature**:
   - Create order → Complete payment → Verify with wrong signature → Error

3. **Wrong User**:
   - User A creates order → User B tries to verify → 403 Forbidden

4. **Webhook**:
   - Create order → Complete payment → Webhook received → Payment updated → Subscription activated

### Integration Testing

Test with Razorpay test keys:
- Use test mode keys from Razorpay dashboard
- Test payments with test cards
- Verify webhook delivery

---

## Deployment

### Environment Variables

Required in production:

```env
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_live_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
```

### Webhook Configuration

1. **Production URL**: `https://backend-gchd.onrender.com/payments/webhook`
2. **Events**: `payment.captured`
3. **Secret**: Set in `RAZORPAY_WEBHOOK_SECRET`

### Database Migration

On first deployment, indexes are created automatically:

```python
# app/database.py - create_indexes()
await db.database.payments.create_index("razorpay_payment_id", unique=True, sparse=True)
```

### Monitoring

Monitor:
- Payment success rate
- Webhook delivery
- Signature verification failures
- Subscription activation rate

---

## Code Summary

### File Structure

```
app/
├── routers/
│   └── payment.py          # Payment API routes
├── services/
│   ├── payment_service.py  # Payment business logic
│   └── subscription_service.py  # Subscription management
├── schemas/
│   └── payment.py          # Request/Response schemas
├── models/
│   └── payment.py          # Database model
└── database.py             # Database indexes
```

### Key Dependencies

- `fastapi`: Web framework
- `razorpay`: Payment gateway SDK
- `motor`: Async MongoDB driver
- `pydantic`: Data validation
- `python-jose`: JWT handling

---

## Best Practices

1. ✅ **Always verify signatures** - Never trust payment data without verification
2. ✅ **Store payment records** - Keep audit trail of all payments
3. ✅ **Handle webhooks idempotently** - Process only if status is "pending"
4. ✅ **Validate user ownership** - Ensure users can only verify their own payments
5. ✅ **Log all errors** - Helps with debugging and monitoring
6. ✅ **Use environment variables** - Never hardcode secrets
7. ✅ **Test with test keys** - Use Razorpay test mode for development

---

## Troubleshooting

### Payment Not Verifying

**Symptoms**: Signature verification fails

**Solutions**:
1. Check if all three fields are correct (order_id, payment_id, signature)
2. Verify Razorpay keys are correct
3. Ensure signature is from Razorpay (not modified)

### Webhook Not Working

**Symptoms**: Webhooks not received or failing

**Solutions**:
1. Check webhook URL is accessible
2. Verify webhook secret matches Razorpay dashboard
3. Check webhook signature verification
4. Review webhook logs in Razorpay dashboard

### Subscription Not Activating

**Symptoms**: Payment verified but subscription not active

**Solutions**:
1. Check subscription service logs
2. Verify `renew_subscription()` is called
3. Check database for subscription record
4. Verify user_id is correct

---

**Last Updated**: After payment system implementation
**Backend URL**: `https://backend-gchd.onrender.com`
**Razorpay Dashboard**: https://dashboard.razorpay.com
