# Deployment Guide for Render

## Backend Deployment on Render

### Environment Variables

Set these environment variables in your Render dashboard:

```bash
MONGODB_URL=mongodb+srv://j4e:Shresth123@jarvis4everyone.xyleu2g.mongodb.net/
DATABASE_NAME=J4E
JWT_SECRET_KEY=1a7d5774a992bc4f8cc1d1af3325327eac8333f6b52d072a282cd0f9281eb16c
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720
REFRESH_TOKEN_EXPIRE_DAYS=7
RAZORPAY_KEY_ID=rzp_live_RfIt7D4y82GUIB
RAZORPAY_KEY_SECRET=6zq5DtwceuC0Vi8XppvZN8uv
RAZORPAY_WEBHOOK_SECRET=s45njkfsj35g
APP_NAME=J4EBackend
DEBUG=True
CORS_ORIGINS=https://frontend-4tbx.onrender.com
DOWNLOAD_FILE_PATH=app/.downloads/jarvis4everyone.zip
```

### Important Notes:

1. **DOWNLOAD_FILE_PATH**: Use forward slashes (`/`) not backslashes (`\`) for Linux/Docker
   - ✅ Correct: `app/.downloads/jarvis4everyone.zip`
   - ❌ Wrong: `app\.downloads\jarvis4everyone.zip`

2. **CORS_ORIGINS**: Must include your frontend URL (no wildcard `*` when using credentials)
   - ✅ Correct: `https://frontend-4tbx.onrender.com`
   - ❌ Wrong: `*` (won't work with credentials)

3. **Port**: Render automatically sets the `PORT` environment variable. The app will use it automatically.

## Frontend Configuration

### ⚠️ CRITICAL: Update Frontend API URL

Your frontend is currently trying to connect to `localhost:8000`, which won't work in production.

**You need to update your frontend code to use the backend's Render URL.**

### Steps to Fix Frontend:

1. **Find where API calls are made** (usually in an API config file or environment file)

2. **Create/Update environment variables** in your frontend:
   ```javascript
   // For development
   VITE_API_URL=http://localhost:8000
   // or
   REACT_APP_API_URL=http://localhost:8000
   
   // For production (after backend is deployed)
   VITE_API_URL=https://your-backend-name.onrender.com
   // or
   REACT_APP_API_URL=https://your-backend-name.onrender.com
   ```

3. **Update API calls** to use the environment variable:
   ```javascript
   // Instead of hardcoded localhost:8000
   const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
   // or for React
   const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
   
   // Then use it in fetch calls
   fetch(`${API_URL}/auth/register`, { ... })
   ```

4. **Redeploy your frontend** on Render with the updated environment variable

### Example Frontend Environment Setup:

**For Vite (Vue/React):**
```env
# .env.production
VITE_API_URL=https://your-backend-name.onrender.com

# .env.local (for local development)
VITE_API_URL=http://localhost:8000
```

**For Create React App:**
```env
# .env.production
REACT_APP_API_URL=https://your-backend-name.onrender.com

# .env.local (for local development)
REACT_APP_API_URL=http://localhost:8000
```

## Deployment Checklist

### Backend:
- [ ] Deploy backend to Render
- [ ] Set all environment variables in Render dashboard
- [ ] Verify `DOWNLOAD_FILE_PATH` uses forward slashes
- [ ] Verify `CORS_ORIGINS` includes frontend URL
- [ ] Test backend health endpoint: `https://your-backend.onrender.com/health`
- [ ] Test API docs: `https://your-backend.onrender.com/docs`

### Frontend:
- [ ] Update API URL to use backend's Render URL
- [ ] Set environment variable for production API URL
- [ ] Update all hardcoded `localhost:8000` references
- [ ] Redeploy frontend
- [ ] Test registration/login flow

## Testing

After deployment, test these endpoints:

1. **Health Check**: `GET https://your-backend.onrender.com/health`
2. **API Docs**: `https://your-backend.onrender.com/docs`
3. **Register**: `POST https://your-backend.onrender.com/auth/register`
4. **Login**: `POST https://your-backend.onrender.com/auth/login`

## Troubleshooting

### CORS Errors
- Make sure `CORS_ORIGINS` includes your exact frontend URL (with `https://`)
- No trailing slashes in CORS_ORIGINS
- Don't use `*` when `allow_credentials=True`

### Connection Refused
- Frontend is still using `localhost:8000` - update to backend's Render URL
- Backend might not be deployed yet - check Render dashboard

### Download File Not Found
- Ensure `DOWNLOAD_FILE_PATH` uses forward slashes: `app/.downloads/jarvis4everyone.zip`
- Upload the zip file to your Render instance or use a persistent disk
