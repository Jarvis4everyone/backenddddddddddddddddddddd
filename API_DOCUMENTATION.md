# Jarvis4Everyone - Backend API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication with two types of tokens:
- **Access Token**: Short-lived (15 minutes), sent in `Authorization` header
- **Refresh Token**: Long-lived (7 days), stored in HttpOnly cookie

### Authentication Flow

1. User registers or logs in
2. Backend returns access token in response body
3. Refresh token is automatically set in HttpOnly cookie
4. Frontend stores access token (localStorage/sessionStorage)
5. Include access token in all protected requests: `Authorization: Bearer <access_token>`
6. When access token expires, use `/auth/refresh` to get a new one

---

## API Endpoints

**Quick Reference:**
- **Authentication**: `/auth/*` - Register, login, refresh token
- **Profile**: `/profile/*` - User profile management
- **Subscriptions**: `/subscriptions/*` - Subscription management
- **Payments**: `/payments/*` - Payment processing
- **Downloads**: `/download/*` - File downloads
- **Contact**: `/contact/*` - Contact form submissions
- **Admin**: `/admin/*` - Admin operations (admin only)

---

### Authentication Endpoints

#### 1. Register User
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

**Note:** The `is_admin` field is not required in the request body. It defaults to `false` for all new users. Only admins can create other admin users.

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

#### 2. Login
**POST** `/auth/login`

Login user and receive access token. Refresh token is automatically set in cookie.

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

**Note:** Refresh token is automatically set in HttpOnly cookie. No need to handle it manually.

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
```json
{
  "detail": "Incorrect email or password"
}
```

---

#### 3. Refresh Access Token
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

#### 4. Get My Profile
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

#### 5. Update My Profile
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

**Note:** Email and `is_admin` fields are ignored if provided. Only name and contact_number can be updated.

**Error Responses:**
- `400 Bad Request`: No valid fields to update
- `401 Unauthorized`: Not authenticated

---

#### 6. Get My Subscription (Profile)
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

#### 7. Get Dashboard Data
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

**Note:** `subscription` will be `null` if user has no subscription. `has_active_subscription` is `true` only if subscription exists, is active, and not expired.

**Error Responses:**
- `401 Unauthorized`: Not authenticated

---

### Subscription Endpoints

#### 8. Get My Subscription
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

#### 9. Renew Subscription
**POST** `/subscriptions/renew`

Renew subscription (can renew even after expiry).

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

---

#### 10. Cancel Subscription
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
- `404 Not Found`: No active subscription found

---

### Payment Endpoints

#### 11. Create Payment Order
**POST** `/payments/create-order`

Create a Razorpay order for payment.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "amount": 999.00,
  "currency": "INR"
}
```

**Response:** `200 OK`
```json
{
  "order_id": "order_ABC123XYZ",
  "amount": 99900,
  "currency": "INR",
  "key_id": "rzp_test_xxxxxxxxxxxxx",
  "payment_id": "507f1f77bcf86cd799439013"
}
```

**Note:** 
- Amount is in paise (multiply by 100)
- Use `order_id` and `key_id` to initialize Razorpay checkout
- Store `payment_id` for verification

---

#### 12. Verify Payment
**POST** `/payments/verify`

Verify Razorpay payment and activate subscription.

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
  "amount": 999.00,
  "currency": "INR",
  "razorpay_order_id": "order_ABC123XYZ",
  "razorpay_payment_id": "pay_DEF456UVW",
  "status": "completed",
  "created_at": "2024-01-15T10:35:00Z"
}
```

**Note:** Subscription is automatically activated after successful verification.

**Error Responses:**
- `400 Bad Request`: Invalid payment signature
- `403 Forbidden`: Payment does not belong to current user
- `404 Not Found`: Payment record not found

---

#### 13. Razorpay Webhook
**POST** `/payments/webhook`

Webhook endpoint for Razorpay payment status updates. Configure this URL in Razorpay dashboard.

**Note:** This endpoint is handled automatically by Razorpay. No frontend integration needed.

---

### Download Endpoints

#### 14. Download File
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

---

### Admin Endpoints

**Note:** All admin endpoints require admin authentication.

#### 15. Get All Users
**GET** `/admin/users?skip=0&limit=100`

Get paginated list of all users with subscription information (admin only). This endpoint includes subscription status for each user, making it easy to see which users have active subscriptions.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100, max: 1000)

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
- `has_active_subscription`: Boolean indicating if user has an active and non-expired subscription (useful for quick filtering in admin panel)

---

#### 16. Get User by ID
**GET** `/admin/users/{user_id}`

Get specific user details with subscription information (admin only).

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
}
```

**Response Fields:**
- `subscription`: Full subscription object if user has a subscription, `null` if no subscription exists
- `has_subscription`: Boolean indicating if user has any subscription record
- `has_active_subscription`: Boolean indicating if user has an active and non-expired subscription

---

#### 17. Create User
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

---

#### 18. Update User
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

---

#### 19. Reset User Password
**POST** `/admin/users/{user_id}/reset-password`

Reset user password (admin only). This logs the user out everywhere.

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

---

#### 20. Delete User
**DELETE** `/admin/users/{user_id}`

Delete user (admin only). Keeps payments with email snapshot.

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

---

#### 21. Activate Subscription (Without Payment)
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

---

#### 22. Extend Subscription
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

---

#### 23. Cancel Subscription (Admin)
**POST** `/admin/subscriptions/{user_id}/cancel`

Cancel user's subscription (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Subscription cancelled successfully"
}
```

---

#### 24. Get All Payments
**GET** `/admin/payments?skip=0&limit=100`

Get paginated list of all payments (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100, max: 1000)

**Response:** `200 OK`
```json
[
  {
    "id": "507f1f77bcf86cd799439013",
    "user_id": "507f1f77bcf86cd799439011",
    "email": "john@example.com",
    "plan_id": "monthly",
    "amount": 999.00,
    "currency": "INR",
    "razorpay_order_id": "order_ABC123XYZ",
    "razorpay_payment_id": "pay_DEF456UVW",
    "status": "completed",
    "created_at": "2024-01-15T10:35:00Z"
  }
]
```

---

#### 25. Get All Contacts
**GET** `/contact/admin/all?skip=0&limit=100&status=new`

Get paginated list of all contact submissions (admin only).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100, max: 1000)
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

---

#### 26. Get Contact by ID
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
- `404 Not Found`: Contact not found

---

#### 27. Update Contact Status
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
- `404 Not Found`: Contact not found
- `400 Bad Request`: Invalid status value

---

#### 28. Delete Contact
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
- `404 Not Found`: Contact not found

---

## Error Handling

### Standard Error Response Format
```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or invalid token
- `403 Forbidden`: Insufficient permissions (e.g., not admin, no subscription)
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Frontend Integration Guide

### 1. Authentication Flow

```javascript
// Login
const login = async (email, password) => {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Important: Include cookies
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  // Store access_token in localStorage
  localStorage.setItem('access_token', data.access_token);
  return data;
};

// Make authenticated requests
const getSubscription = async () => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://localhost:8000/subscriptions/me', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    credentials: 'include'
  });
  return response.json();
};

// Refresh token when access token expires
const refreshToken = async () => {
  const response = await fetch('http://localhost:8000/auth/refresh', {
    method: 'POST',
    credentials: 'include' // Cookie is sent automatically
  });
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  return data;
};
```

### 2. Razorpay Payment Integration

```javascript
// Step 1: Create order
const createOrder = async (amount) => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://localhost:8000/payments/create-order', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ amount, currency: 'INR' })
  });
  return response.json();
};

// Step 2: Initialize Razorpay checkout
const options = {
  key: orderData.key_id,
  amount: orderData.amount,
  currency: orderData.currency,
  order_id: orderData.order_id,
  handler: async function (response) {
    // Step 3: Verify payment
    await verifyPayment({
      razorpay_order_id: response.razorpay_order_id,
      razorpay_payment_id: response.razorpay_payment_id,
      razorpay_signature: response.razorpay_signature
    });
  }
};

const rzp = new Razorpay(options);
rzp.open();

// Step 3: Verify payment
const verifyPayment = async (paymentData) => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://localhost:8000/payments/verify', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(paymentData)
  });
  return response.json();
};
```

### 3. Check Subscription Status

```javascript
// Check if user has active subscription
const checkSubscription = async () => {
  try {
    const subscription = await apiCall('http://localhost:8000/subscriptions/me');
    
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

### 5. Submit Contact Form

```javascript
// Submit contact form (authentication optional)
const submitContact = async (contactData) => {
  const token = localStorage.getItem('access_token');
  const headers = {
    'Content-Type': 'application/json'
  };
  
  // Add authorization header if user is logged in
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch('http://localhost:8000/contact', {
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

// Example usage
submitContact({
  name: 'John Doe',
  email: 'john@example.com',
  subject: 'Question about subscription',
  message: 'I have a question about how the subscription works.'
}).then(data => {
  console.log('Contact submitted:', data);
  alert('Thank you for contacting us! We will get back to you soon.');
}).catch(error => {
  console.error('Error:', error);
  alert('Failed to submit contact form. Please try again.');
});
```

### 6. Download File

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
    const response = await fetch('http://localhost:8000/download/file', {
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

### 4. Error Handling

```javascript
const handleApiError = async (response) => {
  if (!response.ok) {
    const error = await response.json();
    
    if (response.status === 401) {
      // Token expired, try refresh
      try {
        await refreshToken();
        // Retry original request
      } catch (e) {
        // Refresh failed, redirect to login
        window.location.href = '/login';
      }
    }
    
    throw new Error(error.detail || 'An error occurred');
  }
  return response.json();
};

// Enhanced error handler with retry logic
const apiCall = async (url, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const defaultOptions = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers
    },
    credentials: 'include',
    ...options
  };
  
  let response = await fetch(url, defaultOptions);
  
  // Handle token expiry
  if (response.status === 401 && token) {
    try {
      await refreshToken();
      // Retry with new token
      defaultOptions.headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
      response = await fetch(url, defaultOptions);
    } catch (e) {
      // Refresh failed, redirect to login
      window.location.href = '/login';
      return;
    }
  }
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'An error occurred');
  }
  
  return response.json();
};
```

---

## Important Notes

1. **CORS**: Make sure your frontend URL is in `CORS_ORIGINS` in backend `.env`
2. **Cookies**: Always use `credentials: 'include'` in fetch requests to send/receive cookies
3. **Token Storage**: Store access token securely (localStorage/sessionStorage)
4. **Token Refresh**: Implement automatic token refresh on 401 errors
5. **Subscription Check**: Check subscription status before showing download button
6. **Error Messages**: Display user-friendly error messages from `detail` field
7. **Admin Routes**: Only accessible if `is_admin: true` in user object
8. **Admin Field**: The `is_admin` field defaults to `false` for all users. It's automatically set during user creation and stored in the database. Existing users without this field will be updated to `is_admin: false` on server startup.
9. **Subscription Expiry**: Subscriptions are automatically checked for expiry on user login
10. **Payment Verification**: Always verify payment on backend after Razorpay success callback
11. **Password Reset**: When admin resets a user's password, that user is logged out from all devices

---

## Testing

### Interactive API Documentation

Use the interactive API documentation at:
```
http://localhost:8000/docs
```

This provides a Swagger UI where you can test all endpoints directly.

### Health Check

Check if the backend is running:
```
GET http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy"
}
```

### Root Endpoint

Get API information:
```
GET http://localhost:8000/
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
**Solution**: Ensure your frontend URL is added to `CORS_ORIGINS` in backend `.env` file

### Issue: 401 Unauthorized on Protected Routes
**Solution**: 
- Check if access token is included in `Authorization` header
- Verify token hasn't expired (15 minutes)
- Try refreshing token using `/auth/refresh`
- Ensure `credentials: 'include'` is set in fetch options

### Issue: Refresh Token Not Working
**Solution**:
- Ensure cookies are enabled in browser
- Check if `credentials: 'include'` is set in fetch options
- Verify backend is running and cookie settings are correct

### Issue: Payment Verification Fails
**Solution**:
- Ensure you're sending all three fields: `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`
- Verify payment belongs to current user
- Check Razorpay dashboard for payment status

### Issue: Download Returns 403
**Solution**:
- Check if user has an active subscription: `GET /subscriptions/me`
- Verify subscription status is `active` and not expired
- Ensure subscription `end_date` is in the future

---

## Support

For questions or issues, contact the backend team.

**Backend Repository**: Check the codebase for implementation details
**API Docs**: Visit `http://localhost:8000/docs` for interactive API testing

