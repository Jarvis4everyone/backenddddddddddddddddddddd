# Razorpay Configuration Guide

## Error Fix: Connection Issues

### Problem
The error `ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))` occurs when:
- Razorpay API is temporarily unavailable
- Network timeouts
- Connection interruptions

### Solution Implemented
✅ **Retry Logic**: Automatic retry with exponential backoff (3 attempts)
✅ **Async Handling**: Razorpay calls run in thread pool to avoid blocking
✅ **Better Error Handling**: Specific error types with appropriate HTTP status codes
✅ **Logging**: Detailed logs for debugging

### How It Works
1. **First Attempt**: Tries to create order immediately
2. **On Failure**: Waits 1 second, retries
3. **Second Failure**: Waits 2 seconds, retries
4. **Third Failure**: Waits 4 seconds, retries
5. **Final Failure**: Returns appropriate error to user

---

## Razorpay Name and Logo Configuration

### ⚠️ Important: Frontend vs Backend

**The name and logo are configured in the FRONTEND, not the backend.**

### Backend Responsibilities
The backend only provides:
- ✅ `key_id` (Razorpay key ID)
- ✅ `order_id` (Razorpay order ID)
- ✅ `amount` (Payment amount in paise)
- ✅ `currency` (Currency code, e.g., "INR")

### Frontend Responsibilities
The frontend configures:
- ✅ **Name**: Company/product name displayed in Razorpay checkout
- ✅ **Logo**: Company logo displayed in Razorpay checkout
- ✅ **Description**: Payment description
- ✅ **Theme**: Colors and styling
- ✅ **Prefill**: User details (email, phone, etc.)

---

## Frontend Integration Example

### Step 1: Get Order from Backend
```javascript
const response = await fetch('https://backend-hjyy.onrender.com/payments/create-order', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ 
    amount: 299,  // or get from /subscriptions/price
    currency: 'INR' 
  })
});

const orderData = await response.json();
// Returns: { order_id, amount, currency, key_id, payment_id }
```

### Step 2: Initialize Razorpay Checkout (Frontend)
```javascript
// Load Razorpay script: <script src="https://checkout.razorpay.com/v1/checkout.js"></script>

const options = {
  key: orderData.key_id,           // From backend
  amount: orderData.amount,        // From backend (already in paise)
  currency: orderData.currency,    // From backend
  order_id: orderData.order_id,   // From backend
  
  // ⭐ NAME AND LOGO CONFIGURED HERE (Frontend)
  name: 'Jarvis4Everyone',        // Your company/product name
  description: 'Monthly Subscription',  // Payment description
  image: 'https://jarvis4everyone.com/logo.png',  // Your logo URL
  
  // Theme customization (Frontend)
  theme: {
    color: '#3399cc'  // Your brand color
  },
  
  // Prefill user details (Optional, Frontend)
  prefill: {
    name: 'John Doe',
    email: 'user@example.com',
    contact: '9999999999'
  },
  
  // Handler for successful payment (Frontend)
  handler: async function (response) {
    // Verify payment with backend
    await verifyPayment({
      razorpay_order_id: response.razorpay_order_id,
      razorpay_payment_id: response.razorpay_payment_id,
      razorpay_signature: response.razorpay_signature
    });
  },
  
  // Error handler (Frontend)
  modal: {
    ondismiss: function() {
      console.log('Payment cancelled');
    }
  }
};

const rzp = new Razorpay(options);
rzp.open();
```

---

## Complete Frontend Example

```javascript
// Complete payment flow
async function initiatePayment() {
  try {
    // 1. Get subscription price (optional, or use hardcoded)
    const priceResponse = await fetch('https://backend-hjyy.onrender.com/subscriptions/price');
    const priceData = await priceResponse.json();
    
    // 2. Create order
    const orderResponse = await fetch('https://backend-hjyy.onrender.com/payments/create-order', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        amount: priceData.price,
        currency: 'INR' 
      })
    });
    
    if (!orderResponse.ok) {
      throw new Error('Failed to create order');
    }
    
    const orderData = await orderResponse.json();
    
    // 3. Initialize Razorpay with YOUR branding
    const options = {
      key: orderData.key_id,
      amount: orderData.amount,
      currency: orderData.currency,
      order_id: orderData.order_id,
      
      // ⭐ YOUR BRANDING HERE
      name: 'Jarvis4Everyone',
      description: 'Monthly Subscription - ₹299',
      image: 'https://jarvis4everyone.com/assets/logo.png',  // Your logo
      
      theme: {
        color: '#3399cc'  // Your brand color
      },
      
      prefill: {
        email: userEmail,  // From your user data
        name: userName     // From your user data
      },
      
      handler: async function (response) {
        // 4. Verify payment
        const verifyResponse = await fetch('https://backend-hjyy.onrender.com/payments/verify', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature
          })
        });
        
        if (verifyResponse.ok) {
          alert('Payment successful!');
          // Redirect or refresh subscription status
        } else {
          alert('Payment verification failed');
        }
      },
      
      modal: {
        ondismiss: function() {
          console.log('Payment cancelled');
        }
      }
    };
    
    const rzp = new Razorpay(options);
    rzp.open();
    
  } catch (error) {
    console.error('Payment error:', error);
    alert('Error: ' + error.message);
  }
}
```

---

## Logo Requirements

### Recommended Logo Specifications:
- **Format**: PNG or JPG
- **Size**: 200x200 pixels (square)
- **File Size**: < 1MB
- **Background**: Transparent or white
- **URL**: Must be publicly accessible (HTTPS)

### Logo URL Examples:
```javascript
// Good - Public HTTPS URL
image: 'https://jarvis4everyone.com/assets/logo.png'
image: 'https://cdn.jarvis4everyone.com/logo.png'
image: 'https://yourdomain.com/images/logo.png'

// Bad - Local or HTTP
image: '/assets/logo.png'  // Won't work
image: 'http://example.com/logo.png'  // Must be HTTPS
```

---

## Summary

| Configuration | Location | Example |
|--------------|----------|---------|
| **Name** | Frontend | `name: 'Jarvis4Everyone'` |
| **Logo** | Frontend | `image: 'https://jarvis4everyone.com/logo.png'` |
| **Description** | Frontend | `description: 'Monthly Subscription'` |
| **Theme/Colors** | Frontend | `theme: { color: '#3399cc' }` |
| **Key ID** | Backend | Returned in `/payments/create-order` |
| **Order ID** | Backend | Returned in `/payments/create-order` |
| **Amount** | Backend | Returned in `/payments/create-order` |

---

## Backend API Response

When you call `/payments/create-order`, the backend returns:

```json
{
  "order_id": "order_ABC123XYZ",
  "amount": 29900,
  "currency": "INR",
  "key_id": "rzp_live_RfIt7D4y82GUIB",
  "payment_id": "payment_db_id"
}
```

**You use these values in the frontend Razorpay initialization.**

---

## Troubleshooting

### Logo Not Showing?
1. ✅ Ensure logo URL is publicly accessible
2. ✅ Use HTTPS (not HTTP)
3. ✅ Check CORS settings if hosting on different domain
4. ✅ Verify image format (PNG/JPG)
5. ✅ Check image size (< 1MB recommended)

### Name Not Showing?
1. ✅ Check the `name` field in Razorpay options
2. ✅ Ensure it's a string (not null/undefined)
3. ✅ Maximum 127 characters

### Connection Errors?
1. ✅ Backend now has automatic retry logic
2. ✅ Check network connectivity
3. ✅ Verify Razorpay API status
4. ✅ Check backend logs for detailed error messages

---

## Need Help?

- **Backend Issues**: Check backend logs at Render dashboard
- **Frontend Issues**: Check browser console for errors
- **Razorpay Issues**: Check Razorpay dashboard for API status
