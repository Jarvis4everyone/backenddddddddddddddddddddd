# Deploy Changes to Render

Your code is committed and pushed to GitHub. Now you need to deploy it to Render.

## Option 1: Automatic Deployment (Recommended)

If auto-deploy is enabled on Render, it should automatically detect the push to `main` branch and start deploying within 1-2 minutes.

**Check if auto-deploy is working:**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your service: `jarvis4everyone-backend` (or similar)
3. Check the "Events" or "Deployments" tab
4. You should see a new deployment triggered by the latest commit `ec9901d`

**If you see a deployment in progress:**
- Wait for it to complete (usually 2-5 minutes)
- Check the logs to ensure it builds successfully
- Once deployed, your changes will be live at `https://backend-hjyy.onrender.com`

---

## Option 2: Manual Deployment Trigger

If auto-deploy didn't trigger, manually trigger a deployment:

### Steps:

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Log in to your account

2. **Select Your Service**
   - Click on your backend service (likely named `jarvis4everyone-backend` or similar)
   - Or find it in the services list

3. **Trigger Manual Deploy**
   - Look for a **"Manual Deploy"** button or **"Deploy latest commit"** option
   - Click it to start a new deployment
   - Render will pull the latest code from GitHub and rebuild

4. **Monitor Deployment**
   - Watch the build logs in real-time
   - Wait for the deployment to complete
   - Check for any errors in the logs

---

## Option 3: Verify Environment Variables

Before deploying, ensure your Render service has the correct environment variables set:

### Required Environment Variables:

1. **MongoDB Configuration:**
   - `MONGODB_URL` - Your MongoDB connection string
   - `DATABASE_NAME` - Database name (default: `J4E` or `saas_subscription_db`)

2. **JWT Configuration:**
   - `JWT_SECRET_KEY` - Your JWT secret key
   - `JWT_ALGORITHM` - Usually `HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time
   - `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiration

3. **Razorpay Configuration:**
   - `RAZORPAY_KEY_ID` - Your Razorpay key ID
   - `RAZORPAY_KEY_SECRET` - Your Razorpay key secret
   - `RAZORPAY_WEBHOOK_SECRET` - Razorpay webhook secret

4. **Application Configuration:**
   - `APP_NAME` - Application name
   - `DEBUG` - Set to `False` for production
   - `CORS_ORIGINS` - Comma-separated list of allowed origins
     - Should include: `https://jarvis4everyone.com,https://frontend-4tbx.onrender.com`
   - `DOWNLOAD_FILE_PATH` - Path to download file (default: `./.downloads/jarvis4everyone.zip`)
   - `SUBSCRIPTION_PRICE` - Subscription price in INR (default: `299.0`)

5. **Port Configuration:**
   - `PORT` - Automatically set by Render (don't manually set this)

### How to Update Environment Variables:

1. Go to your service in Render Dashboard
2. Click on **"Environment"** tab
3. Add or update environment variables
4. Click **"Save Changes"**
5. Render will automatically redeploy with new environment variables

---

## Option 4: Force Redeploy via Render Dashboard

If you want to force a fresh deployment:

1. Go to Render Dashboard → Your Service
2. Click on **"Manual Deploy"** → **"Deploy latest commit"**
3. Or click **"Clear build cache & deploy"** for a completely fresh build

---

## Verify Deployment

After deployment completes, verify your changes are live:

### 1. Check CORS Configuration:
```bash
curl https://backend-hjyy.onrender.com/cors-info
```

Expected response should include `https://jarvis4everyone.com` in the CORS origins list.

### 2. Check Health:
```bash
curl https://backend-hjyy.onrender.com/health
```

Should return: `{"status": "healthy"}`

### 3. Check Subscription Price:
```bash
curl https://backend-hjyy.onrender.com/subscriptions/price
```

Should return the subscription price (default: 299 INR).

---

## Troubleshooting

### If deployment fails:

1. **Check Build Logs:**
   - Go to your service → "Logs" tab
   - Look for error messages
   - Common issues:
     - Missing environment variables
     - Build errors
     - Dependency installation failures

2. **Check Environment Variables:**
   - Ensure all required variables are set
   - Check for typos in variable names
   - Verify values are correct

3. **Check GitHub Connection:**
   - Ensure Render is connected to your GitHub repository
   - Verify the branch is set to `main`
   - Check repository permissions

4. **Clear Build Cache:**
   - Sometimes cached builds cause issues
   - Use "Clear build cache & deploy" option

---

## Quick Checklist

- [ ] Code is pushed to GitHub (✅ Done - commit `ec9901d`)
- [ ] Render service is connected to GitHub repository
- [ ] Auto-deploy is enabled (or manually trigger deployment)
- [ ] All environment variables are set correctly
- [ ] Deployment completes successfully
- [ ] Service is live and accessible
- [ ] CORS configuration includes `jarvis4everyone.com`
- [ ] Test endpoints are working

---

## Expected Deployment Time

- **Build time:** 2-5 minutes
- **Deploy time:** 1-2 minutes
- **Total:** 3-7 minutes

---

## After Deployment

Once deployed, your changes will be live:
- Updated CORS configuration with `jarvis4everyone.com`
- Removed old documentation files
- All latest code changes

Your backend will be accessible at: `https://backend-hjyy.onrender.com`
