# Frontend Subscription Pricing Guide

## Overview

The subscription price is configurable via backend environment variables. The frontend should fetch the price from the backend API to ensure consistency.

## API Endpoint

### Get Subscription Price

**Endpoint**: `GET /subscriptions/price`

**Authentication**: Not required (public endpoint)

**Response**:
```json
{
  "price": 299.0,
  "currency": "INR",
  "price_in_paise": 29900
}
```

**Response Fields**:
- `price`: Subscription price in rupees (float)
- `currency`: Currency code (always "INR")
- `price_in_paise`: Price in paise (integer) - use this for Razorpay

## Implementation Guide

### Step 1: Fetch Subscription Price

Create a service or utility function to fetch the price:

```javascript
// src/services/subscriptionService.js
import { getApiUrl } from '../config/api';

class SubscriptionService {
  // Cache the price to avoid multiple API calls
  static priceCache = null;
  static cacheTimestamp = null;
  static CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  async getPrice() {
    // Return cached price if still valid
    if (this.priceCache && this.cacheTimestamp) {
      const now = Date.now();
      if (now - this.cacheTimestamp < this.CACHE_DURATION) {
        return this.priceCache;
      }
    }

    const response = await fetch(getApiUrl('subscriptions/price'), {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Failed to fetch subscription price');
    }

    const data = await response.json();
    
    // Cache the result
    this.priceCache = data;
    this.cacheTimestamp = Date.now();
    
    return data;
  }

  // Get price in rupees (for display)
  async getPriceInRupees() {
    const priceData = await this.getPrice();
    return priceData.price;
  }

  // Get price in paise (for Razorpay)
  async getPriceInPaise() {
    const priceData = await this.getPrice();
    return priceData.price_in_paise;
  }
}

export default new SubscriptionService();
```

### Step 2: Display Price in UI

```javascript
// Example: Pricing Component
import { useState, useEffect } from 'react';
import SubscriptionService from '../services/subscriptionService';

function PricingCard() {
  const [price, setPrice] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPrice() {
      try {
        const priceData = await SubscriptionService.getPrice();
        setPrice(priceData.price);
      } catch (error) {
        console.error('Error fetching price:', error);
        // Fallback to default price
        setPrice(299);
      } finally {
        setLoading(false);
      }
    }

    fetchPrice();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="pricing-card">
      <h2>Monthly Subscription</h2>
      <div className="price">
        ₹{price?.toFixed(2) || '299.00'}
      </div>
      <p>per month</p>
    </div>
  );
}
```

### Step 3: Use Price for Payment

```javascript
// Example: Payment Component
import SubscriptionService from '../services/subscriptionService';
import PaymentService from '../services/paymentService';

async function handlePayment() {
  try {
    // Get price from backend
    const priceData = await SubscriptionService.getPrice();
    const amountInRupees = priceData.price;
    
    // Create payment order with the price from backend
    const orderData = await PaymentService.createOrder(
      amountInRupees, // Use price from backend
      'INR'
    );
    
    // Initialize Razorpay with the order
    PaymentService.initializeRazorpay(orderData, onSuccess, onError);
  } catch (error) {
    console.error('Payment error:', error);
    alert('Error: ' + error.message);
  }
}
```

## Important Notes

### 1. Always Fetch Price from Backend

❌ **Don't hardcode the price:**
```javascript
// BAD
const price = 299;
```

✅ **Fetch from backend:**
```javascript
// GOOD
const priceData = await SubscriptionService.getPrice();
const price = priceData.price;
```

### 2. Use Price in Paise for Razorpay

Razorpay requires amounts in paise (smallest currency unit). The API provides `price_in_paise` for this:

```javascript
// The API already converts to paise
const priceData = await SubscriptionService.getPrice();
// priceData.price_in_paise = 29900 (for ₹299)

// When creating Razorpay order, the backend handles conversion
// But if you need to display or validate, use price_in_paise
```

### 3. Cache the Price

Since the price doesn't change frequently, cache it to reduce API calls:

```javascript
// Cache for 5-10 minutes
// Refresh on page reload or when user navigates to pricing page
```

### 4. Error Handling

Always have a fallback price in case the API fails:

```javascript
try {
  const price = await SubscriptionService.getPrice();
} catch (error) {
  // Fallback to default
  const price = 299; // Default fallback
  console.error('Failed to fetch price, using default:', error);
}
```

## Complete Example: Payment Flow

```javascript
import { useState, useEffect } from 'react';
import SubscriptionService from '../services/subscriptionService';
import PaymentService from '../services/paymentService';

function SubscribeButton() {
  const [price, setPrice] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Fetch price on component mount
    SubscriptionService.getPrice()
      .then(data => setPrice(data.price))
      .catch(() => setPrice(299)); // Fallback
  }, []);

  const handleSubscribe = async () => {
    if (!price) {
      alert('Price not available. Please refresh the page.');
      return;
    }

    setLoading(true);
    try {
      // Get fresh price data (in case it changed)
      const priceData = await SubscriptionService.getPrice();
      
      // Create payment order
      const orderData = await PaymentService.createOrder(
        priceData.price,
        'INR'
      );
      
      // Initialize Razorpay
      PaymentService.initializeRazorpay(
        orderData,
        (response) => {
          // Payment successful
          alert('Payment successful! Your subscription is now active.');
          window.location.reload();
        },
        (error) => {
          // Payment failed
          alert('Payment failed: ' + error.message);
        }
      );
    } catch (error) {
      console.error('Error:', error);
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="price-display">
        {price ? `₹${price.toFixed(2)}` : 'Loading...'} / month
      </div>
      <button 
        onClick={handleSubscribe} 
        disabled={loading || !price}
      >
        {loading ? 'Processing...' : 'Subscribe Now'}
      </button>
    </div>
  );
}
```

## Environment Configuration

### Backend Environment Variable

The backend uses the `SUBSCRIPTION_PRICE` environment variable:

```env
SUBSCRIPTION_PRICE=299
```

- **Default**: 299 (if not set)
- **Format**: Number (can be decimal, e.g., 299.99)
- **Unit**: INR (Rupees)

### Frontend Environment Variables

No frontend environment variables needed for price - always fetch from backend API.

## Testing

### Test Price Fetching

```javascript
// Test in browser console
fetch('https://backend-gchd.onrender.com/subscriptions/price')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

Expected response:
```json
{
  "price": 299.0,
  "currency": "INR",
  "price_in_paise": 29900
}
```

### Test Payment Flow

1. Fetch price from `/subscriptions/price`
2. Use price to create payment order
3. Verify Razorpay shows correct amount
4. Complete payment
5. Verify subscription is activated

## Troubleshooting

### Issue: Price Not Loading

**Symptoms**: Price shows as "Loading..." or undefined

**Solutions**:
1. Check network tab - is API call successful?
2. Verify backend is running: `GET /health`
3. Check CORS configuration
4. Use fallback price: `const price = 299;`

### Issue: Wrong Price Displayed

**Symptoms**: Shows different price than expected

**Solutions**:
1. Clear price cache: `SubscriptionService.priceCache = null;`
2. Check backend environment variable: `SUBSCRIPTION_PRICE`
3. Verify API response: `GET /subscriptions/price`
4. Check if price was updated in backend but frontend is using cached value

### Issue: Payment Amount Mismatch

**Symptoms**: Razorpay shows different amount

**Solutions**:
1. Ensure you're using `price` (in rupees) when calling `createOrder`
2. Backend converts to paise automatically
3. Don't multiply by 100 in frontend - backend handles it

## Best Practices

1. ✅ **Always fetch price from backend** - Never hardcode
2. ✅ **Cache the price** - Reduce API calls
3. ✅ **Have fallback** - Use default (299) if API fails
4. ✅ **Refresh cache** - On page reload or pricing page visit
5. ✅ **Handle errors gracefully** - Show fallback price if fetch fails
6. ✅ **Use price_in_paise** - For any calculations or validations
7. ✅ **Display price clearly** - Show currency symbol and format properly

## API Reference

### GET /subscriptions/price

**Description**: Get current subscription price

**Authentication**: Not required

**Response**:
```json
{
  "price": 299.0,
  "currency": "INR",
  "price_in_paise": 29900
}
```

**Error Responses**:
- `500 Internal Server Error`: Backend error

**Example Usage**:
```javascript
const response = await fetch('https://backend-gchd.onrender.com/subscriptions/price');
const data = await response.json();
console.log(`Price: ₹${data.price} (${data.price_in_paise} paise)`);
```

---

**Last Updated**: After subscription price configuration
**Backend URL**: `https://backend-gchd.onrender.com`
**Default Price**: ₹299.00
