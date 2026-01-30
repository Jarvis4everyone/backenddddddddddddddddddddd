# Complete Frontend Fix Guide - Jarvis4Everyone

This guide will help you fix all frontend issues to work with your deployed backend at `https://backend-hjyy.onrender.com`.

## Table of Contents
1. [Environment Variables Setup](#environment-variables-setup)
2. [API Configuration](#api-configuration)
3. [Update All API Calls](#update-all-api-calls)
4. [CORS Configuration](#cors-configuration)
5. [Authentication Flow](#authentication-flow)
6. [Payment Integration (Razorpay)](#payment-integration-razorpay)
7. [Error Handling](#error-handling)
8. [Common Issues & Solutions](#common-issues--solutions)
9. [Complete Code Examples](#complete-code-examples)

---

## Environment Variables Setup

### Step 1: Create Environment Files

#### For Vite (Vue/React with Vite):

**`.env.production`** (for production):
```env
VITE_API_URL=https://backend-hjyy.onrender.com
```

**`.env.local`** or **`.env.development`** (for local development):
```env
VITE_API_URL=http://localhost:8000
```

#### For Create React App:

**`.env.production`**:
```env
REACT_APP_API_URL=https://backend-hjyy.onrender.com
```

**`.env.local`**:
```env
REACT_APP_API_URL=http://localhost:8000
```

#### For Next.js:

**`.env.production`**:
```env
NEXT_PUBLIC_API_URL=https://backend-hjyy.onrender.com
```

**`.env.local`**:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 2: Set Environment Variable in Render (Frontend)

1. Go to your frontend service on Render: `https://frontend-4tbx.onrender.com`
2. Navigate to **Environment** tab
3. Add/Update environment variable:
   - **For Vite**: `VITE_API_URL` = `https://backend-hjyy.onrender.com`
   - **For React**: `REACT_APP_API_URL` = `https://backend-hjyy.onrender.com`
   - **For Next.js**: `NEXT_PUBLIC_API_URL` = `https://backend-hjyy.onrender.com`
4. **Redeploy** your frontend

---

## API Configuration

### Create API Configuration File

Create `src/config/api.js` (or `src/config/api.ts` for TypeScript):

```javascript
// For Vite
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// For Create React App
// const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// For Next.js
// const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_BASE_URL = API_URL;

// Helper to get full API endpoint
export const getApiUrl = (endpoint) => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${API_BASE_URL}/${cleanEndpoint}`;
};

export default API_BASE_URL;
```

---

## Update All API Calls

### Step 1: Find All Hardcoded URLs

Search your codebase for:
- `localhost:8000`
- `127.0.0.1:8000`
- `http://localhost:8000`
- Any hardcoded backend URLs

**Command to search** (in your frontend directory):
```bash
# Windows PowerShell
Select-String -Path "src/**/*.{js,jsx,ts,tsx}" -Pattern "localhost:8000"

# Linux/Mac
grep -r "localhost:8000" src/
```

### Step 2: Replace with Environment Variable

**Before:**
```javascript
fetch('http://localhost:8000/auth/register', { ... })
```

**After:**
```javascript
import { getApiUrl } from './config/api';

fetch(getApiUrl('auth/register'), { ... })
```

---

## CORS Configuration

### Frontend CORS Requirements

All API calls **MUST** include `credentials: 'include'` to work with CORS:

```javascript
fetch(getApiUrl('auth/login'), {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include', // ⚠️ CRITICAL: Must include this
  body: JSON.stringify(data)
})
```

### Why CORS Fails Without credentials

- Backend uses `allow_credentials=True`
- This requires explicit origin matching
- Without `credentials: 'include'`, cookies won't be sent/received

---

## Authentication Flow

### Complete Authentication Service

Create `src/services/authService.js`:

```javascript
import { getApiUrl } from '../config/api';

class AuthService {
  // Register new user
  async register(userData) {
    const response = await fetch(getApiUrl('auth/register'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        name: userData.name,
        email: userData.email,
        contact_number: userData.contact_number,
        password: userData.password,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    return response.json();
  }

  // Login
  async login(email, password) {
    const response = await fetch(getApiUrl('auth/login'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for cookies
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    
    // Store access token
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
    }

    return data;
  }

  // Get current user profile
  async getCurrentUser() {
    const token = this.getToken();
    if (!token) {
      throw new Error('No access token found');
    }

    const response = await fetch(getApiUrl('profile/me'), {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired, try refresh
        await this.refreshToken();
        // Retry request
        return this.getCurrentUser();
      }
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get user');
    }

    return response.json();
  }

  // Refresh access token
  async refreshToken() {
    const response = await fetch(getApiUrl('auth/refresh'), {
      method: 'POST',
      credentials: 'include', // Cookie is sent automatically
    });

    if (!response.ok) {
      // Refresh failed, clear token and redirect to login
      this.logout();
      throw new Error('Session expired. Please login again.');
    }

    const data = await response.json();
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
    }

    return data;
  }

  // Logout
  logout() {
    localStorage.removeItem('access_token');
    // Optionally call backend logout endpoint
  }

  // Get stored token
  getToken() {
    return localStorage.getItem('access_token');
  }

  // Check if user is authenticated
  isAuthenticated() {
    return !!this.getToken();
  }
}

export default new AuthService();
```

---

## Payment Integration (Razorpay)

### Complete Payment Service

Create `src/services/paymentService.js`:

```javascript
import { getApiUrl } from '../config/api';
import AuthService from './authService';

class PaymentService {
  // Create Razorpay order
  async createOrder(amount, currency = 'INR') {
    const token = AuthService.getToken();
    if (!token) {
      throw new Error('User must be logged in');
    }

    const response = await fetch(getApiUrl('payments/create-order'), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        amount: amount,
        currency: currency,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create order');
    }

    return response.json();
  }

  // Initialize Razorpay checkout
  async initializeRazorpay(orderData, onSuccess, onError) {
    const options = {
      key: orderData.key_id, // From backend response
      amount: orderData.amount,
      currency: orderData.currency,
      name: 'Jarvis4Everyone',
      description: 'Subscription Payment',
      order_id: orderData.order_id,
      handler: async (response) => {
        try {
          await this.verifyPayment({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          onSuccess(response);
        } catch (error) {
          onError(error);
        }
      },
      prefill: {
        // You can prefill user details if available
      },
      theme: {
        color: '#3399cc',
      },
      modal: {
        ondismiss: () => {
          console.log('Payment cancelled');
        },
      },
    };

    const razorpay = new window.Razorpay(options);
    razorpay.open();
  }

  // Verify payment
  async verifyPayment(verifyData) {
    const token = AuthService.getToken();
    if (!token) {
      throw new Error('User must be logged in');
    }

    const response = await fetch(getApiUrl('payments/verify'), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        razorpay_order_id: verifyData.razorpay_order_id,
        razorpay_payment_id: verifyData.razorpay_payment_id,
        razorpay_signature: verifyData.razorpay_signature,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Payment verification failed');
    }

    return response.json();
  }
}

export default new PaymentService();
```

### Payment Component Example

```javascript
import { useState } from 'react';
import PaymentService from '../services/paymentService';
import AuthService from '../services/authService';

function PaymentButton() {
  const [loading, setLoading] = useState(false);

  const handlePayment = async () => {
    try {
      setLoading(true);
      
      // Create order
      const orderData = await PaymentService.createOrder(50000); // ₹500.00 in paise
      
      // Initialize Razorpay
      PaymentService.initializeRazorpay(
        orderData,
        async (response) => {
          // Payment successful
          console.log('Payment successful:', response);
          alert('Payment successful! Your subscription is now active.');
          // Refresh subscription status
          window.location.reload();
        },
        (error) => {
          // Payment failed
          console.error('Payment error:', error);
          alert('Payment failed: ' + error.message);
        }
      );
    } catch (error) {
      console.error('Error creating order:', error);
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handlePayment} disabled={loading}>
      {loading ? 'Processing...' : 'Subscribe Now'}
    </button>
  );
}
```

### Add Razorpay Script to HTML

In your `index.html` or `_document.js` (Next.js):

```html
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
```

---

## Error Handling

### Global API Error Handler

Create `src/utils/apiErrorHandler.js`:

```javascript
import AuthService from '../services/authService';

export const handleApiError = async (response, retryCallback = null) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'An error occurred',
    }));

    // Handle 401 Unauthorized (Token expired)
    if (response.status === 401) {
      try {
        // Try to refresh token
        await AuthService.refreshToken();
        
        // Retry original request if callback provided
        if (retryCallback) {
          return await retryCallback();
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        AuthService.logout();
        window.location.href = '/login';
        throw new Error('Session expired. Please login again.');
      }
    }

    // Handle other errors
    throw new Error(error.detail || `Error: ${response.status}`);
  }

  return response.json();
};

// Enhanced fetch wrapper with automatic retry
export const apiCall = async (endpoint, options = {}) => {
  const token = AuthService.getToken();
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    credentials: 'include',
    ...options,
  };

  const url = endpoint.startsWith('http') 
    ? endpoint 
    : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/${endpoint}`;

  let response = await fetch(url, defaultOptions);

  // Handle 401 with retry
  if (response.status === 401 && token) {
    try {
      await AuthService.refreshToken();
      // Retry with new token
      defaultOptions.headers['Authorization'] = `Bearer ${AuthService.getToken()}`;
      response = await fetch(url, defaultOptions);
    } catch (e) {
      AuthService.logout();
      window.location.href = '/login';
      throw new Error('Session expired');
    }
  }

  return handleApiError(response);
};
```

---

## Common Issues & Solutions

### Issue 1: CORS Errors

**Error:**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Solution:**
1. ✅ Ensure `credentials: 'include'` in all fetch requests
2. ✅ Verify backend has `CORS_ORIGINS=https://frontend-4tbx.onrender.com`
3. ✅ Check backend is deployed and running
4. ✅ No trailing slashes in CORS_ORIGINS

### Issue 2: Connection Refused

**Error:**
```
Failed to load resource: net::ERR_CONNECTION_REFUSED
```

**Solution:**
1. ✅ Replace all `localhost:8000` with environment variable
2. ✅ Set `VITE_API_URL` (or equivalent) in Render environment
3. ✅ Redeploy frontend after setting environment variable

### Issue 3: 401 Unauthorized

**Error:**
```
401 Unauthorized
```

**Solution:**
1. ✅ Check if access token is included in Authorization header
2. ✅ Implement automatic token refresh on 401
3. ✅ Ensure `credentials: 'include'` is set
4. ✅ Check token expiration (15 minutes for access token)

### Issue 4: Payment Not Working

**Error:**
```
Payment verification failed
```

**Solution:**
1. ✅ Ensure Razorpay script is loaded: `<script src="https://checkout.razorpay.com/v1/checkout.js"></script>`
2. ✅ Verify all three fields are sent: `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`
3. ✅ Check Razorpay keys are correct (live keys for production)
4. ✅ Verify payment belongs to current user

### Issue 5: Subscription Not Found

**Error:**
```
No subscription found
```

**Solution:**
1. ✅ Check if payment was verified successfully
2. ✅ Verify subscription was created after payment
3. ✅ Check subscription status: `GET /subscriptions/me`

### Issue 6: Environment Variable Not Working

**Error:**
Still using localhost in production

**Solution:**
1. ✅ Restart dev server after changing `.env` files
2. ✅ For Vite: Variables must start with `VITE_`
3. ✅ For React: Variables must start with `REACT_APP_`
4. ✅ For Next.js: Variables must start with `NEXT_PUBLIC_`
5. ✅ Set environment variable in Render dashboard
6. ✅ Redeploy after setting environment variable

---

## Complete Code Examples

### Example: Complete API Service

`src/services/apiService.js`:

```javascript
import { getApiUrl } from '../config/api';
import AuthService from './authService';

class ApiService {
  async request(endpoint, options = {}) {
    const token = AuthService.getToken();
    
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      credentials: 'include',
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    let response = await fetch(getApiUrl(endpoint), config);

    // Handle 401 with token refresh
    if (response.status === 401 && token) {
      try {
        await AuthService.refreshToken();
        config.headers['Authorization'] = `Bearer ${AuthService.getToken()}`;
        response = await fetch(getApiUrl(endpoint), config);
      } catch (e) {
        AuthService.logout();
        throw new Error('Session expired');
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: 'An error occurred',
      }));
      throw new Error(error.detail || `Error: ${response.status}`);
    }

    return response.json();
  }

  // Subscription methods
  async getSubscription() {
    return this.request('subscriptions/me');
  }

  // Contact methods
  async submitContact(data) {
    return this.request('contact', {
      method: 'POST',
      body: data,
    });
  }

  // Download methods
  async downloadFile() {
    const token = AuthService.getToken();
    const response = await fetch(getApiUrl('download/file'), {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Download failed');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'jarvis4everyone.zip';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }
}

export default new ApiService();
```

---

## Deployment Checklist

### Before Deploying:

- [ ] All `localhost:8000` replaced with environment variable
- [ ] Environment variable set in Render frontend dashboard
- [ ] All fetch requests include `credentials: 'include'`
- [ ] Razorpay script added to HTML
- [ ] Error handling implemented
- [ ] Token refresh logic implemented
- [ ] Tested locally with production API URL

### After Deploying:

- [ ] Test registration flow
- [ ] Test login flow
- [ ] Test payment flow
- [ ] Test subscription check
- [ ] Test download (if applicable)
- [ ] Check browser console for errors
- [ ] Verify CORS headers in Network tab

---

## Quick Reference

### API Endpoints

- **Register**: `POST /auth/register`
- **Login**: `POST /auth/login`
- **Refresh Token**: `POST /auth/refresh`
- **Get Profile**: `GET /profile/me`
- **Get Subscription**: `GET /subscriptions/me`
- **Create Payment**: `POST /payments/create-order`
- **Verify Payment**: `POST /payments/verify`
- **Download**: `GET /download/file`
- **Contact**: `POST /contact`

### Required Headers

```javascript
{
  'Content-Type': 'application/json',
  'Authorization': 'Bearer <access_token>', // For protected routes
}
```

### Required Options

```javascript
{
  credentials: 'include', // Always required
}
```

---

## Support

If you're still experiencing issues:

1. Check browser console for specific errors
2. Check Network tab to see request/response details
3. Verify backend is running: `https://backend-hjyy.onrender.com/health`
4. Check CORS config: `https://backend-hjyy.onrender.com/cors-info`
5. Review backend logs in Render dashboard

---

**Last Updated**: After backend deployment fixes
**Backend URL**: `https://backend-hjyy.onrender.com`
**Frontend URL**: `https://frontend-4tbx.onrender.com`
