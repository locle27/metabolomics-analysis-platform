# OAuth Configuration Fix - UPDATED

## Issue Fixed: 
Updated OAuth configuration to use Google's automatic discovery and proper endpoints.

## Current Configuration (CORRECT):
- **App Route**: `/callback` (matches Google Console setting)
- **Google Console Authorized redirect URIs**: `http://localhost:5000/callback`

## Changes Made:
1. **Updated OAuth config** to use `server_metadata_url` for automatic endpoint discovery
2. **Fixed user info extraction** with fallback methods
3. **Updated callback route** from `/login/authorized` to `/callback` to match Google Console

## Current Setup Status:
✅ OAuth endpoints configured with Google's discovery URL
✅ Callback route matches Google Console (`/callback`) 
✅ User info extraction with multiple fallback methods
✅ Proper error handling for all OAuth steps

## Google Cloud Console Should Have:
- Authorized redirect URIs: `http://localhost:5000/callback`

## Test Steps:
1. Restart Flask application: `python app.py`
2. Go to: http://localhost:5000/login
3. Click "Login with Gmail" 
4. Should now work without "Invalid URL 'None'" error

The OAuth should now work correctly with the improved configuration.