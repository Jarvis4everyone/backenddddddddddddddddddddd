# Frontend Fix - Update API URL

## Problem
Your frontend at `https://frontend-4tbx.onrender.com/` is trying to connect to `localhost:8000` instead of your backend URL `https://backend-hjyy.onrender.com/`.

## Solution

You need to update your frontend code to use the backend's Render URL.

### Step 1: Find Your API Configuration

Search for `localhost:8000` in your frontend codebase. Common locations:
- `src/config.js` or `src/config.ts`
- `src/api/index.js` or `src/api/index.ts`
- `src/utils/api.js` or `src/utils/api.ts`
- `.env` or `.env.production` files
- `vite.config.js` or `vite.config.ts`
- `src/constants.js` or `src/constants.ts`

### Step 2: Create/Update Environment Variables

#### For Vite (Vue/React with Vite):

Create or update `.env.production`:
```env
VITE_API_URL=https://backend-hjyy.onrender.com
```

Create or update `.env.local` (for local development):
```env
VITE_API_URL=http://localhost:8000
```

#### For Create React App:

Create or update `.env.production`:
```env
REACT_APP_API_URL=https://backend-hjyy.onrender.com
```

Create or update `.env.local`:
```env
REACT_APP_API_URL=http://localhost:8000
```

#### For Next.js:

Create or update `.env.production`:
```env
NEXT_PUBLIC_API_URL=https://backend-hjyy.onrender.com
```

Create or update `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 3: Update Your API Configuration File

Create or update your API config file (e.g., `src/config.js`):

```javascript
// For Vite
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// For Create React App
// const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// For Next.js
// const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default API_URL;
```

### Step 4: Update All API Calls

Replace all hardcoded `localhost:8000` references:

**Before:**
```javascript
fetch('http://localhost:8000/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})
```

**After:**
```javascript
import API_URL from './config'; // or wherever your config is

fetch(`${API_URL}/auth/register`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include', // Important for cookies
  body: JSON.stringify(data)
})
```

### Step 5: Set Environment Variable in Render

1. Go to your frontend service on Render: `https://frontend-4tbx.onrender.com/`
2. Go to **Environment** tab
3. Add environment variable:
   - **Key**: `VITE_API_URL` (or `REACT_APP_API_URL` or `NEXT_PUBLIC_API_URL` depending on your framework)
   - **Value**: `https://backend-hjyy.onrender.com`
4. Save and redeploy

### Step 6: Common Files to Check

Search for these patterns in your frontend code:

```bash
# Search for localhost:8000
grep -r "localhost:8000" src/
grep -r "127.0.0.1:8000" src/
grep -r "http://localhost:8000" src/
```

### Example: Complete API Service File

```javascript
// src/services/api.js
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_URL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Important for cookies
    };

    // Add auth token if available
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, config);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'An error occurred');
    }

    return response.json();
  }

  async register(data) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async login(data) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Add other methods...
}

export default new ApiService();
```

### Quick Fix: Global Find and Replace

If you want a quick fix, you can do a find and replace in your frontend codebase:

**Find:** `http://localhost:8000`
**Replace:** `https://backend-hjyy.onrender.com`

**OR** (better approach):
**Find:** `http://localhost:8000`
**Replace:** `${API_URL}` or `import.meta.env.VITE_API_URL`

Then make sure to import/define `API_URL` at the top of files that use it.

## Verification

After making changes:

1. **Local Testing**: Set your local env to `http://localhost:8000` and test locally
2. **Production**: Set Render env var to `https://backend-hjyy.onrender.com` and redeploy
3. **Check Browser Console**: Should see requests going to `https://backend-hjyy.onrender.com` not `localhost:8000`

## Important Notes

- Always use `credentials: 'include'` in fetch requests to send/receive cookies
- The backend CORS is already configured to allow `https://frontend-4tbx.onrender.com`
- Make sure there are no trailing slashes in the API URL
- Test both registration and login flows after updating
