# Jarvis4Everyone - Backend API Documentation

## Base URL

**Production:**
```
https://backend-hjyy.onrender.com
```

**Local Development:**
```
http://localhost:8000
```

**Interactive API Documentation:**
- Production: `https://backend-hjyy.onrender.com/docs`
- Local: `http://localhost:8000/docs`

---

## Table of Contents

1. [Authentication](#authentication)
2. [API Endpoints](#api-endpoints)
   - [Public Endpoints](#public-endpoints)
   - [Authentication Endpoints](#authentication-endpoints)
   - [Profile Endpoints](#profile-endpoints)
   - [Subscription Endpoints](#subscription-endpoints)
   - [Payment Endpoints](#payment-endpoints)
   - [Download Endpoints](#download-endpoints)
   - [Contact Endpoints](#contact-endpoints)
   - [Admin Endpoints](#admin-endpoints)
3. [Error Handling](#error-handling)
4. [Frontend Integration Guide](#frontend-integration-guide)
5. [Testing](#testing)
6. [Common Issues & Solutions](#common-issues--solutions)

---

## Authentication

The API uses JWT (JSON Web Tokens) for authentication with two types of tokens:

- **Access Token**: Short-lived (configurable, default: 15 minutes), sent in `Authorization` header
- **Refresh Token**: Long-lived (7 days), stored in HttpOnly cookie

### Authentication Flow

1. User registers or logs in
2. Backend returns access token in response body
3. Refresh token is automatically set in HttpOnly cookie
4. Frontend stores access token (localStorage/sessionStorage)
5. Include access token in all protected requests: `Authorization: Bearer <access_token>`
6. When access token expires, use `/auth/refresh` to get a new one

### Token Configuration

- **Access Token Expiry**: Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 15 minutes)
- **Refresh Token Expiry**: 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)

---

## API Endpoints

### Public Endpoints

These endpoints do not require authentication.

#### 1. Root Endpoint
**GET** `/`

Get API information.

**Response:** `200 OK`
```json
{
  "message": "Jarvis4Everyone Backend API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

#### 2. Health Check
**GET** `/health`

Check if the backend is running.

**Response:** `200 OK`
```json
{
  "status": "healthy"
}
```

#### 3. CORS Info (Debug)
**GET** `/cors-info`

Get CORS configuration information (for debugging).

**Response:** `200 OK`
```json
{
  "cors_origins": "https://frontend-4tbx.onrender.com",
  "cors_origins_list": ["https://frontend-4tbx.onrender.com"],
  "allowed_origins_count": 1
}
```

#### 4. Get Subscription Price
**GET** `/subscriptions/price`

Get current subscription price (public endpoint, no authentication required).

**Response:** `200 OK`
```json
{
  "price": 299.0,
  "currency": "INR",
  "price_in_paise": 29900
}
```

**Note:** Price is configurable via `SUBSCRIPTION_PRICE` environment variable (default: 299.0 INR).

---

### Authentication Endpoints

#### 5. Register User
**POST** `/auth/register`

Register a new user account. The `is_admin` field is automatically set to `false` by default.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "contact_number": "+1234567890",
  "password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "John Doe",
  "email": "john@example.com",
  "contact_number": "+1234567890",
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_login": null
}
```

**Error Responses:**
- `400 Bad Request`: Email already registered
```json
{
  "detail": "Email already registered"
}
```

---

#### 6. Login
**POST** `/auth/login`

Login user and receive access token. Refresh token is automatically set in HttpOnly cookie.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Note:** 
- Refresh token is automatically set in HttpOnly cookie
- Cookie settings:
  - `httponly=True` (not accessible via JavaScript)
  - `secure=True` in production (HTTPS only)
  - `samesite="lax"`
  - Expires in 7 days

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
```json
{
  "detail": "Incorrect email or password"
}
```

---

#### 7. Refresh Access Token
**POST** `/auth/refresh`

Get a new access token using the refresh token from cookie.

**Request:** No body required. Refresh token is read from cookie automatically.

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired refresh token
```json
{
  "detail": "Invalid or expired refresh token"
}
```

---

### Profile Endpoints

All profile endpoints require authentication.

#### 8. Get My Profile
**GET** `/profile/me`

Get current user's profile information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "John Doe",
  "email": "john@example.com",
  "contact_number": "+1234567890",
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T14:22:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated

---

#### 9. Update My Profile
**PUT** `/profile/me`

Update current user's profile (name and contact_number only). Email and admin status cannot be changed by user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:** (all fields optional)
```json
{
  "name": "John Updated",
  "contact_number": "+1234567890"
}
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "John Updated",
  "email": "john@example.com",
  "contact_number": "+1234567890",
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:30:00Z",
  "last_login": "2024-01-20T14:22:00Z"
}
```

**Note:** 
- Email and `is_admin` fields are ignored if provided
- Only name and contact_number can be updated by the user

**Error Responses:**
- `400 Bad Request`: No valid fields to update
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: User not found

---

#### 10. Get My Subscription (Profile)
**GET** `/profile/subscription`

Get current user's subscription status (same as `/subscriptions/me`).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "plan_id": "monthly",
  "status": "active",
  "start_date": "2024-01-15T10:30:00Z",
  "end_date": "2024-02-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "cancelled_at": null
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: No subscription found

---

#### 11. Get Dashboard Data
**GET** `/profile/dashboard`

Get complete dashboard data including profile and subscription in one request.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "contact_number": "+1234567890",
    "is_admin": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-20T14:22:00Z"
  },
  "subscription": {
    "id": "507f1f77bcf86cd799439012",
    "user_id": "507f1f77bcf86cd799439011",
    "plan_id": "monthly",
    "status": "active",
    "start_date": "2024-01-15T10:30:00Z",
    "end_date": "2024-02-15T10:30:00Z",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "cancelled_at": null
  },
  "has_active_subscription": true
}
```

**Note:** 
- `subscription` will be `null` if user has no subscription
- `has_active_subscription` is `true` only if subscription exists, is active, and not expired

**Error Responses:**
- `401 Unauthorized`: Not authenticated

---

### Subscription Endpoints

#### 12. Get Subscription Price (Public)
**GET** `/subscriptions/price`

Get current subscription price. This is a public endpoint (no authentication required).

**Response:** `200 OK`
```json
{
  "price": 299.0,
  "currency": "INR",
  "price_in_paise": 29900
}
```

**Note:** 
- Price is configurable via `SUBSCRIPTION_PRICE` environment variable
- Default price: ₹299.00 (29900 paise)
- Use `price_in_paise` for Razorpay integration

---

#### 13. Get My Subscription
**GET** `/subscriptions/me`

Get current user's subscription status.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "plan_id": "monthly",
  "status": "active",
  "start_date": "2024-01-15T10:30:00Z",
  "end_date": "2024-02-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "cancelled_at": null
}
```

**Status Values:**
- `active`: Subscription is active and not expired
- `expired`: Subscription has passed end_date
- `cancelled`: Subscription was cancelled

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: No subscription found

---

#### 14. Renew Subscription
**POST** `/subscriptions/renew`

Renew subscription (can renew even after expiry). This cancels any existing subscriptions and creates a new one.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "months": 1
}
```

**Response:** `201 Created`
```json
{
  "id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "plan_id": "monthly",
  "status": "active",
  "start_date": "2024-01-20T10:30:00Z",
  "end_date": "2024-02-20T10:30:00Z",
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:30:00Z",
  "cancelled_at": null
}
```

**Note:** 
- Cancels any existing active or expired subscriptions
- Creates a new subscription starting from current date
- `months` parameter determines subscription duration

---

#### 15. Cancel Subscription
**POST** `/subscriptions/cancel`

Cancel current user's active subscription.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:** No body required

**Response:** `200 OK`
```json
{
  "message": "Subscription cancelled successfully"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: No active subscription found

---

### Payment Endpoints

#### 16. Create Payment Order
**POST** `/payments/create-order`

Create a Razorpay order for payment. This creates a payment record in the database with status "pending".

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "amount": 299.00,
  "currency": "INR"
}
```

**Response:** `200 OK`
```json
{
  "order_id": "order_ABC123XYZ",
  "amount": 29900,
  "currency": "INR",
  "key_id": "rzp_live_xxxxxxxxxxxxx",
  "payment_id": "507f1f77bcf86cd799439013"
}
```

**Note:** 
- `amount` in request is in rupees (e.g., 299.00)
- `amount` in response is in paise (e.g., 29900)
- Use `order_id` and `key_id` to initialize Razorpay checkout
- Store `payment_id` for verification
- Payment record is created with status "pending"

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `400 Bad Request`: Invalid request data

---

#### 17. Verify Payment
**POST** `/payments/verify`

Verify Razorpay payment and activate subscription. This endpoint:
1. Verifies payment signature
2. Updates payment status to "completed"
3. Activates subscription (1 month)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "razorpay_order_id": "order_ABC123XYZ",
  "razorpay_payment_id": "pay_DEF456UVW",
  "razorpay_signature": "signature_GHI789RST"
}
```

**Response:** `200 OK`
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
  "razorpay_signature": "signature_GHI789RST",
  "status": "completed",
  "created_at": "2024-01-15T10:35:00Z"
}
```

**Note:** 
- Subscription is automatically activated after successful verification
- Grants 1 month subscription access
- Payment signature is verified using Razorpay utility

**Error Responses:**
- `400 Bad Request`: Invalid payment signature
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Payment does not belong to current user
- `404 Not Found`: Payment record not found

---

#### 18. Razorpay Webhook
**POST** `/payments/webhook`

Webhook endpoint for Razorpay payment status updates. Configure this URL in Razorpay dashboard.

**Headers:**
```
X-Razorpay-Signature: <webhook_signature>
```

**Request Body:** (Razorpay webhook payload)
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
        "status": "captured"
      }
    }
  }
}
```

**Response:** `200 OK`
```json
{
  "status": "success"
}
```

**Note:** 
- This endpoint is called automatically by Razorpay
- No frontend integration needed
- Webhook signature is verified
- Payment status is updated and subscription is activated if payment was pending

**Error Responses:**
- `400 Bad Request`: Missing or invalid webhook signature
- `500 Internal Server Error`: Error processing webhook

**Webhook Setup:**
1. Go to Razorpay Dashboard → Settings → Webhooks
2. Add webhook URL: `https://backend-hjyy.onrender.com/payments/webhook`
3. Select events: `payment.captured`
4. Copy webhook secret and set `RAZORPAY_WEBHOOK_SECRET` in environment variables

---

### Download Endpoints

#### 19. Download File
**GET** `/download/file`

Download Jarvis4Everyone .zip file. Requires active subscription.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
- Returns file download (binary)
- Content-Type: `application/zip`
- Filename: `jarvis4everyone.zip`

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: No subscription or subscription expired
```json
{
  "detail": "No subscription found. Please purchase a subscription to download."
}
```
or
```json
{
  "detail": "Your subscription has expired. Please renew to download."
}
```
- `500 Internal Server Error`: Download file not available

---

### Contact Endpoints

#### 20. Submit Contact Form
**POST** `/contact`

Submit a contact form. Authentication is optional - if user is logged in, their user_id will be associated with the contact.

**Headers:** (Optional)
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Question about subscription",
  "message": "I have a question about how the subscription works."
}
```

**Response:** `201 Created`
```json
{
  "id": "507f1f77bcf86cd799439015",
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Question about subscription",
  "message": "I have a question about how the subscription works.",
  "status": "new",
  "user_id": "507f1f77bcf86cd799439011",
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:30:00Z"
}
```

**Note:** 
- `user_id` will be `null` if user is not logged in
- Status defaults to "new"
- This is a public endpoint (authentication optional)

---

### Admin Endpoints

**Note:** All admin endpoints require admin authentication (`is_admin: true`).

#### 21. Get All Users
**GET** `/admin/users?skip=0&limit=100`

Get paginated list of all users with subscription information (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0, min: 0)
- `limit` (optional): Number of records to return (default: 100, min: 1, max: 1000)

**Response:** `200 OK`
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "contact_number": "+1234567890",
    "is_admin": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-20T14:22:00Z",
    "subscription": {
      "id": "507f1f77bcf86cd799439012",
      "user_id": "507f1f77bcf86cd799439011",
      "plan_id": "monthly",
      "status": "active",
      "start_date": "2024-01-15T10:30:00Z",
      "end_date": "2024-02-15T10:30:00Z",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "cancelled_at": null
    },
    "has_subscription": true,
    "has_active_subscription": true
  },
  {
    "id": "507f1f77bcf86cd799439013",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "contact_number": "+1234567891",
    "is_admin": false,
    "created_at": "2024-01-16T10:30:00Z",
    "updated_at": "2024-01-16T10:30:00Z",
    "last_login": null,
    "subscription": null,
    "has_subscription": false,
    "has_active_subscription": false
  }
]
```

**Response Fields:**
- `subscription`: Full subscription object if user has a subscription (active, expired, or cancelled), `null` if no subscription exists
- `has_subscription`: Boolean indicating if user has any subscription record
- `has_active_subscription`: Boolean indicating if user has an active and non-expired subscription

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user

---

#### 22. Get User by ID
**GET** `/admin/users/{user_id}`

Get specific user details (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "John Doe",
  "email": "john@example.com",
  "contact_number": "+1234567890",
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T14:22:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user
- `404 Not Found`: User not found

---

#### 23. Create User
**POST** `/admin/users`

Create a new user (admin only). The `is_admin` field defaults to `false` if not provided.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "contact_number": "+1234567891",
  "password": "securepassword123",
  "is_admin": false
}
```

**Note:** The `is_admin` field is optional and defaults to `false`. Only admins can create other admin users by setting `is_admin: true`.

**Response:** `201 Created`
```json
{
  "id": "507f1f77bcf86cd799439014",
  "name": "Jane Doe",
  "email": "jane@example.com",
  "contact_number": "+1234567891",
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_login": null
}
```

**Error Responses:**
- `400 Bad Request`: Email already registered
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user

---

#### 24. Update User
**PUT** `/admin/users/{user_id}`

Update user details (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:** (all fields optional)
```json
{
  "name": "John Updated",
  "email": "johnupdated@example.com",
  "contact_number": "+1234567890",
  "is_admin": false
}
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "John Updated",
  "email": "johnupdated@example.com",
  "contact_number": "+1234567890",
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:30:00Z",
  "last_login": "2024-01-20T14:22:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: No fields to update or email already registered
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user
- `404 Not Found`: User not found

---

#### 25. Reset User Password
**POST** `/admin/users/{user_id}/reset-password`

Reset user password (admin only). This logs the user out everywhere by invalidating all refresh tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "new_password": "newsecurepassword123"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset successfully. User logged out everywhere."
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user
- `404 Not Found`: User not found

---

#### 26. Delete User
**DELETE** `/admin/users/{user_id}`

Delete user (admin only). Keeps payments with email snapshot. Admins cannot delete themselves.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "User deleted successfully"
}
```

**Error Responses:**
- `400 Bad Request`: Cannot delete yourself
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user
- `404 Not Found`: User not found

---

#### 27. Get All Subscriptions
**GET** `/admin/subscriptions?skip=0&limit=100`

Get paginated list of all subscriptions (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0, min: 0)
- `limit` (optional): Number of records to return (default: 100, min: 1, max: 1000)

**Response:** `200 OK`
```json
[
  {
    "id": "507f1f77bcf86cd799439012",
    "user_id": "507f1f77bcf86cd799439011",
    "plan_id": "monthly",
    "status": "active",
    "start_date": "2024-01-15T10:30:00Z",
    "end_date": "2024-02-15T10:30:00Z",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "cancelled_at": null
  }
]
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user

---

#### 28. Activate Subscription (Without Payment)
**POST** `/admin/subscriptions/activate`

Activate subscription for a user without payment (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "months": 1
}
```

**Response:** `201 Created`
```json
{
  "id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "plan_id": "monthly",
  "status": "active",
  "start_date": "2024-01-20T10:30:00Z",
  "end_date": "2024-02-20T10:30:00Z",
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:30:00Z",
  "cancelled_at": null
}
```

**Note:** This cancels any existing subscriptions and creates a new one.

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user

---

#### 29. Extend Subscription
**POST** `/admin/subscriptions/{user_id}/extend`

Extend user's active subscription (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "months": 1
}
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "plan_id": "monthly",
  "status": "active",
  "start_date": "2024-01-15T10:30:00Z",
  "end_date": "2024-03-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:30:00Z",
  "cancelled_at": null
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user
- `404 Not Found`: Active subscription not found

---

#### 30. Cancel Subscription (Admin)
**POST** `/admin/subscriptions/{user_id}/cancel`

Cancel user's subscription (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:** No body required

**Response:** `200 OK`
```json
{
  "message": "Subscription cancelled successfully"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user
- `404 Not Found`: Active subscription not found

---

#### 31. Get All Payments
**GET** `/admin/payments?skip=0&limit=100`

Get paginated list of all payments (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0, min: 0)
- `limit` (optional): Number of records to return (default: 100, min: 1, max: 1000)

**Response:** `200 OK`
```json
[
  {
    "id": "507f1f77bcf86cd799439013",
    "user_id": "507f1f77bcf86cd799439011",
    "email": "john@example.com",
    "plan_id": "monthly",
    "amount": 299.00,
    "currency": "INR",
    "razorpay_order_id": "order_ABC123XYZ",
    "razorpay_payment_id": "pay_DEF456UVW",
    "razorpay_signature": "signature_GHI789RST",
    "status": "completed",
    "created_at": "2024-01-15T10:35:00Z"
  }
]
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user

---

#### 32. Get All Contacts
**GET** `/contact/admin/all?skip=0&limit=100&status=new`

Get paginated list of all contact submissions (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0, min: 0)
- `limit` (optional): Number of records to return (default: 100, min: 1, max: 1000)
- `status` (optional): Filter by status (`new`, `read`, `replied`, `archived`)

**Response:** `200 OK`
```json
[
  {
    "id": "507f1f77bcf86cd799439015",
    "name": "John Doe",
    "email": "john@example.com",
    "subject": "Question about subscription",
    "message": "I have a question about how the subscription works.",
    "status": "new",
    "user_id": "507f1f77bcf86cd799439011",
    "created_at": "2024-01-20T10:30:00Z",
    "updated_at": "2024-01-20T10:30:00Z"
  }
]
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user

---

#### 33. Get Contact by ID
**GET** `/contact/admin/{contact_id}`

Get specific contact submission details (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439015",
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Question about subscription",
  "message": "I have a question about how the subscription works.",
  "status": "new",
  "user_id": "507f1f77bcf86cd799439011",
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user
- `404 Not Found`: Contact not found

---

#### 34. Update Contact Status
**PATCH** `/contact/admin/{contact_id}/status`

Update contact submission status (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "status": "read"
}
```

**Status Values:**
- `new`: New submission (default)
- `read`: Admin has read the message
- `replied`: Admin has replied to the message
- `archived`: Contact has been archived

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439015",
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Question about subscription",
  "message": "I have a question about how the subscription works.",
  "status": "read",
  "user_id": "507f1f77bcf86cd799439011",
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:35:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid status value
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user
- `404 Not Found`: Contact not found

---

#### 35. Delete Contact
**DELETE** `/contact/admin/{contact_id}`

Delete a contact submission (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Contact deleted successfully"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin user
- `404 Not Found`: Contact not found

---

## Error Handling

### Standard Error Response Format

All errors follow this format:
```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data or validation error
- `401 Unauthorized`: Authentication required or invalid/expired token
- `403 Forbidden`: Insufficient permissions (e.g., not admin, no subscription)
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Common Error Scenarios

#### Authentication Errors

**401 Unauthorized** - Missing or invalid token:
```json
{
  "detail": "Not authenticated"
}
```

**401 Unauthorized** - Expired access token:
```json
{
  "detail": "Invalid or expired refresh token"
}
```

#### Validation Errors

**400 Bad Request** - Invalid request body:
```json
{
  "detail": "Validation error: field 'email' is required"
}
```

#### Authorization Errors

**403 Forbidden** - Not an admin:
```json
{
  "detail": "Admin access required"
}
```

**403 Forbidden** - No subscription:
```json
{
  "detail": "No subscription found. Please purchase a subscription to download."
}
```

#### Not Found Errors

**404 Not Found** - Resource doesn't exist:
```json
{
  "detail": "User not found"
}
```

---

## Frontend Integration Guide

### 1. Authentication Flow

#### Register
```javascript
const register = async (userData) => {
  const response = await fetch('https://backend-hjyy.onrender.com/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      name: userData.name,
      email: userData.email,
      contact_number: userData.contact_number,
      password: userData.password
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }
  
  return response.json();
};
```

#### Login
```javascript
const login = async (email, password) => {
  const response = await fetch('https://backend-hjyy.onrender.com/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Important: Include cookies
    body: JSON.stringify({ email, password })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }
  
  const data = await response.json();
  // Store access_token in localStorage
  localStorage.setItem('access_token', data.access_token);
  return data;
};
```

#### Make Authenticated Requests
```javascript
const getSubscription = async () => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('https://backend-hjyy.onrender.com/subscriptions/me', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    credentials: 'include'
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }
  
  return response.json();
};
```

#### Refresh Token
```javascript
const refreshToken = async () => {
  const response = await fetch('https://backend-hjyy.onrender.com/auth/refresh', {
    method: 'POST',
    credentials: 'include' // Cookie is sent automatically
  });
  
  if (!response.ok) {
    // Refresh failed, redirect to login
    localStorage.removeItem('access_token');
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  return data;
};
```

### 2. Razorpay Payment Integration

#### Step 1: Get Subscription Price
```javascript
const getPrice = async () => {
  const response = await fetch('https://backend-hjyy.onrender.com/subscriptions/price');
  return response.json();
};
```

#### Step 2: Create Payment Order
```javascript
const createOrder = async (amount) => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('https://backend-hjyy.onrender.com/payments/create-order', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify({ amount, currency: 'INR' })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create order');
  }
  
  return response.json();
};
```

#### Step 3: Initialize Razorpay Checkout
```javascript
// Load Razorpay script first: <script src="https://checkout.razorpay.com/v1/checkout.js"></script>

const initializeRazorpay = async () => {
  try {
    // Get price from backend
    const priceData = await getPrice();
    
    // Create order
    const orderData = await createOrder(priceData.price);
    
    // Initialize Razorpay
    const options = {
      key: orderData.key_id,
      amount: orderData.amount, // Already in paise
      currency: orderData.currency,
      name: 'Jarvis4Everyone',
      description: 'Subscription Payment',
      order_id: orderData.order_id,
      handler: async function (response) {
        // Step 4: Verify payment
        await verifyPayment({
          razorpay_order_id: response.razorpay_order_id,
          razorpay_payment_id: response.razorpay_payment_id,
          razorpay_signature: response.razorpay_signature
        });
      },
      prefill: {
        // Optional: Prefill user details
      },
      theme: {
        color: '#3399cc'
      }
    };
    
    const rzp = new Razorpay(options);
    rzp.open();
  } catch (error) {
    console.error('Payment error:', error);
    alert('Error: ' + error.message);
  }
};
```

#### Step 4: Verify Payment
```javascript
const verifyPayment = async (paymentData) => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('https://backend-hjyy.onrender.com/payments/verify', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify(paymentData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Payment verification failed');
  }
  
  const result = await response.json();
  alert('Payment successful! Your subscription is now active.');
  return result;
};
```

### 3. Check Subscription Status

```javascript
const checkSubscription = async () => {
  try {
    const subscription = await getSubscription();
    
    if (subscription.status === 'active') {
      // Check if not expired
      const endDate = new Date(subscription.end_date);
      const now = new Date();
      
      if (endDate > now) {
        return { active: true, subscription };
      } else {
        return { active: false, expired: true, subscription };
      }
    }
    
    return { active: false, subscription };
  } catch (error) {
    if (error.message.includes('No subscription found')) {
      return { active: false, noSubscription: true };
    }
    throw error;
  }
};
```

### 4. Submit Contact Form

```javascript
const submitContact = async (contactData) => {
  const token = localStorage.getItem('access_token');
  const headers = {
    'Content-Type': 'application/json'
  };
  
  // Add authorization header if user is logged in
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch('https://backend-hjyy.onrender.com/contact', {
    method: 'POST',
    headers: headers,
    credentials: 'include',
    body: JSON.stringify({
      name: contactData.name,
      email: contactData.email,
      subject: contactData.subject,
      message: contactData.message
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to submit contact form');
  }
  
  return response.json();
};
```

### 5. Download File

```javascript
const downloadFile = async () => {
  try {
    // First check subscription
    const subStatus = await checkSubscription();
    
    if (!subStatus.active) {
      alert('You need an active subscription to download');
      return;
    }
    
    // Proceed with download
    const token = localStorage.getItem('access_token');
    const response = await fetch('https://backend-hjyy.onrender.com/download/file', {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      credentials: 'include'
    });
    
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'jarvis4everyone.zip';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } else {
      const error = await response.json();
      alert(error.detail);
    }
  } catch (error) {
    console.error('Download error:', error);
    alert('Failed to download file. Please try again.');
  }
};
```

### 6. Error Handling with Auto Retry

```javascript
const handleApiError = async (response) => {
  if (!response.ok) {
    const error = await response.json();
    
    if (response.status === 401) {
      // Token expired, try refresh
      try {
        await refreshToken();
        // Retry original request (caller should handle this)
        return { retry: true };
      } catch (e) {
        // Refresh failed, redirect to login
        window.location.href = '/login';
        throw new Error('Session expired');
      }
    }
    
    throw new Error(error.detail || 'An error occurred');
  }
  
  return response.json();
};

// Enhanced API call with automatic retry
const apiCall = async (url, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers
    },
    credentials: 'include',
    ...options
  };
  
  let response = await fetch(url, defaultOptions);
  
  // Handle 401 with retry
  if (response.status === 401 && token) {
    try {
      await refreshToken();
      // Retry with new token
      defaultOptions.headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
      response = await fetch(url, defaultOptions);
    } catch (e) {
      window.location.href = '/login';
      throw new Error('Session expired');
    }
  }
  
  return handleApiError(response);
};
```

---

## Testing

### Interactive API Documentation

Use the interactive API documentation (Swagger UI) at:
- **Production**: `https://backend-hjyy.onrender.com/docs`
- **Local**: `http://localhost:8000/docs`

This provides a Swagger UI where you can test all endpoints directly.

### Health Check

Check if the backend is running:
```bash
curl https://backend-hjyy.onrender.com/health
```

Response:
```json
{
  "status": "healthy"
}
```

### CORS Info

Check CORS configuration:
```bash
curl https://backend-hjyy.onrender.com/cors-info
```

Response:
```json
{
  "cors_origins": "https://frontend-4tbx.onrender.com",
  "cors_origins_list": ["https://frontend-4tbx.onrender.com"],
  "allowed_origins_count": 1
}
```

### Root Endpoint

Get API information:
```bash
curl https://backend-hjyy.onrender.com/
```

Response:
```json
{
  "message": "Jarvis4Everyone Backend API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

## Common Issues & Solutions

### Issue: CORS Errors

**Error:**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Solution:**
1. Ensure your frontend URL is added to `CORS_ORIGINS` in backend environment variables
2. Check CORS config: `GET /cors-info`
3. Verify frontend is using `credentials: 'include'` in all fetch requests
4. No trailing slashes in CORS_ORIGINS

### Issue: 401 Unauthorized on Protected Routes

**Error:**
```
401 Unauthorized
```

**Solution:**
1. Check if access token is included in `Authorization` header
2. Verify token hasn't expired (check `ACCESS_TOKEN_EXPIRE_MINUTES`)
3. Try refreshing token using `/auth/refresh`
4. Ensure `credentials: 'include'` is set in fetch options
5. Check if token is stored correctly in localStorage

### Issue: Refresh Token Not Working

**Error:**
```
Invalid or expired refresh token
```

**Solution:**
1. Ensure cookies are enabled in browser
2. Check if `credentials: 'include'` is set in fetch options
3. Verify backend is running and cookie settings are correct
4. Check if refresh token cookie is being sent (browser DevTools → Application → Cookies)

### Issue: Payment Verification Fails

**Error:**
```
Invalid payment signature
```

**Solution:**
1. Ensure you're sending all three fields: `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`
2. Verify payment belongs to current user
3. Check Razorpay dashboard for payment status
4. Ensure payment data hasn't been tampered with
5. Verify Razorpay keys are correct (test vs live)

### Issue: Download Returns 403

**Error:**
```
No subscription found. Please purchase a subscription to download.
```

**Solution:**
1. Check if user has a subscription: `GET /subscriptions/me`
2. Verify subscription status is `active` and not expired
3. Ensure subscription `end_date` is in the future
4. Check if subscription was cancelled

### Issue: Subscription Price Not Loading

**Error:**
```
Failed to fetch subscription price
```

**Solution:**
1. Check if `/subscriptions/price` endpoint is accessible (public endpoint)
2. Verify backend is running
3. Check `SUBSCRIPTION_PRICE` environment variable is set
4. Use fallback price (299) if API fails

---

## Important Notes

1. **CORS**: Make sure your frontend URL is in `CORS_ORIGINS` in backend environment variables
2. **Cookies**: Always use `credentials: 'include'` in fetch requests to send/receive cookies
3. **Token Storage**: Store access token securely (localStorage/sessionStorage)
4. **Token Refresh**: Implement automatic token refresh on 401 errors
5. **Subscription Check**: Check subscription status before showing download button
6. **Error Messages**: Display user-friendly error messages from `detail` field
7. **Admin Routes**: Only accessible if `is_admin: true` in user object
8. **Admin Field**: The `is_admin` field defaults to `false` for all users. It's automatically set during user creation and stored in the database.
9. **Subscription Expiry**: Subscriptions are automatically checked for expiry
10. **Payment Verification**: Always verify payment on backend after Razorpay success callback
11. **Password Reset**: When admin resets a user's password, that user is logged out from all devices
12. **Subscription Price**: Configurable via `SUBSCRIPTION_PRICE` environment variable (default: 299.0 INR)
13. **Access Token Expiry**: Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 15 minutes)

---

## Support

For questions or issues, contact the backend team.

**Backend Repository**: Check the codebase for implementation details  
**API Docs**: Visit `https://backend-hjyy.onrender.com/docs` for interactive API testing  
**Backend URL**: `https://backend-hjyy.onrender.com`  
**Frontend URL**: `https://frontend-4tbx.onrender.com`

---

**Last Updated**: January 2025  
**API Version**: 1.0.0
