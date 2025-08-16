# 🔑 Google OAuth Setup for Railway Domain

## ❌ Current Issue: OAuth Client Not Found (Error 401: invalid_client)

The Google OAuth configuration needs to be updated for the Railway domain `httpsphenikaa-lipidomics-analysis.xyz`.

## 🔧 Fix Required in Google Cloud Console

### **Step 1: Update Authorized Redirect URIs**

Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials) and update your OAuth 2.0 client:

**Current OAuth Client ID**: `your_google_client_id_here`

**Add these Authorized Redirect URIs:**
```
https://httpsphenikaa-lipidomics-analysis.xyz/google-callback
https://httpsphenikaa-lipidomics-analysis.xyz/callback
https://httpsphenikaa-lipidomics-analysis.xyz/auth
https://httpsphenikaa-lipidomics-analysis.xyz/auth/google/callback
```

**Add these Authorized JavaScript Origins:**
```
https://httpsphenikaa-lipidomics-analysis.xyz
```

### **Step 2: Railway Environment Variables**

Ensure these are set in Railway:
```bash
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

### **Step 3: Test OAuth Flow**

After updating Google Console:
1. Visit: `https://httpsphenikaa-lipidomics-analysis.xyz/google-login`
2. Should redirect to Google login
3. After Google auth, should redirect back to Railway domain
4. User should be logged in automatically

## 🚨 Important Notes

- Changes in Google Cloud Console may take a few minutes to propagate
- Make sure the Railway domain exactly matches what's in Google Console
- Test with an incognito/private browser window to avoid cached auth issues

## 🔍 Debug OAuth Issues

If OAuth still fails:
1. Check browser developer console for redirect errors
2. Verify the exact redirect URI in the error message
3. Ensure Railway environment variables are set correctly
4. Test with `/oauth-debug` endpoint for configuration details