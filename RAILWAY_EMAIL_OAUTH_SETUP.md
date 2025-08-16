# 🚀 Railway Email & OAuth Configuration Guide

## 📧 Complete Email & Authentication Testing Setup

This guide shows you exactly how to configure Railway environment variables for testing all email and OAuth features in your Metabolomics Platform.

## 🔑 Required Railway Environment Variables

### **🗄️ Database Configuration**
```bash
DATABASE_URL=postgresql://postgres:VmyAveAhkGVOFlSiVBWgyIEAUbKAXEPi@mainline.proxy.rlwy.net:36647/lipid-data
```

### **🛡️ Application Security**
```bash
SECRET_KEY=prod-metabolomics-secure-key-2025-railway
FLASK_ENV=production
ENVIRONMENT=production
RAILWAY_ENVIRONMENT=true
```

### **🔐 Google OAuth Configuration**
```bash
GOOGLE_CLIENT_ID=your_google_client_id_from_cloud_console
GOOGLE_CLIENT_SECRET=your_google_client_secret_from_cloud_console
```

### **📧 Gmail SMTP Configuration**
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_gmail_address@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MAIL_DEFAULT_SENDER=your_gmail_address@gmail.com
```


### **🌐 Production Domain Settings**
```bash
CUSTOM_DOMAIN=httpsphenikaa-lipidomics-analysis.xyz
PROD_OAUTH_BASE_URL=https://httpsphenikaa-lipidomics-analysis.xyz
```

### **🎯 OAuth Redirect Configuration**
```bash
OAUTH_REDIRECT_URI_PROD=https://httpsphenikaa-lipidomics-analysis.xyz/auth
OAUTH_REDIRECT_URI_PROD_ALT=https://httpsphenikaa-lipidomics-analysis.xyz/callback
```

### **🧪 Demo & Testing Settings**
```bash
DEMO_ENABLED=true
PROD_USE_DEMO_LOGIN=true
```

## 🎯 **Features Now Available for Testing**

### **✅ Email Features**
1. **User Registration** → Email verification required
2. **Forgot Password** → Password reset emails
3. **Consultation Requests** → Admin + user confirmation emails
4. **Admin Email Testing** → `/test-email` route
5. **Email Status API** → `/email-status` route

### **✅ Authentication Features**  
1. **Google OAuth** → Complete Google login integration
2. **Email/Password** → Traditional registration with verification
3. **Password Reset** → Secure token-based reset system
4. **Demo Login** → Instant admin access for testing

### **✅ Scheduling Features**
1. **Consultation Requests** → Complete form submission
2. **Email Notifications** → Both admin and user emails
3. **Request Management** → Admin panel integration

## 🚀 **Testing URLs for Railway**

### **🏠 Core System Tests**
```
✅ https://httpsphenikaa-lipidomics-analysis.xyz/
✅ https://httpsphenikaa-lipidomics-analysis.xyz/schedule
✅ https://httpsphenikaa-lipidomics-analysis.xyz/api/database-view
```

### **🔐 Authentication Tests**
```
🎯 https://httpsphenikaa-lipidomics-analysis.xyz/auth/register
🎯 https://httpsphenikaa-lipidomics-analysis.xyz/auth/login
🎯 https://httpsphenikaa-lipidomics-analysis.xyz/auth/forgot-password
🎯 https://httpsphenikaa-lipidomics-analysis.xyz/demo-login
🎯 https://httpsphenikaa-lipidomics-analysis.xyz/login/callback
```

### **📧 Email System Tests**
```
📮 https://httpsphenikaa-lipidomics-analysis.xyz/test-email (Admin required)
📮 https://httpsphenikaa-lipidomics-analysis.xyz/email-status (Admin required)
```

### **📊 Platform Features**
```
🔬 https://httpsphenikaa-lipidomics-analysis.xyz/lipid-selection
🔬 https://httpsphenikaa-lipidomics-analysis.xyz/dual-chart-view?lipids=100,101
👨‍💼 https://httpsphenikaa-lipidomics-analysis.xyz/admin
```

## 📋 **Step-by-Step Testing Guide**

### **Step 1: Basic Setup Verification**
1. Visit homepage: `https://httpsphenikaa-lipidomics-analysis.xyz/`
2. Check database: `https://httpsphenikaa-lipidomics-analysis.xyz/api/database-view`
3. Verify Phenikaa design loads correctly

### **Step 2: Demo Admin Access**
1. Go to: `https://httpsphenikaa-lipidomics-analysis.xyz/demo-login`
2. Should instantly log you in as admin
3. Check admin panel: `/admin`

### **Step 3: Email System Testing**
1. As admin, visit: `https://httpsphenikaa-lipidomics-analysis.xyz/test-email`
2. Check your Gmail inbox for test email
3. Visit: `https://httpsphenikaa-lipidomics-analysis.xyz/email-status` for service status

### **Step 4: User Registration Testing**
1. Log out from demo account
2. Go to: `https://httpsphenikaa-lipidomics-analysis.xyz/auth/register`
3. Register with a real email address
4. Check email for verification link
5. Click verification link to activate account

### **Step 5: Password Reset Testing**
1. Go to: `https://httpsphenikaa-lipidomics-analysis.xyz/auth/forgot-password`
2. Enter your email address
3. Check email for reset link
4. Follow reset process

### **Step 6: Scheduling System Testing**
1. Visit: `https://httpsphenikaa-lipidomics-analysis.xyz/schedule`
2. Fill out consultation request form
3. Submit form
4. Check both admin email and user confirmation email

### **Step 7: Google OAuth Testing**
1. Go to: `https://httpsphenikaa-lipidomics-analysis.xyz/auth/login`
2. Click Google sign-in button
3. Complete OAuth flow
4. Should create account and log in automatically

## 🔧 **Google Cloud Console OAuth Setup**

### **Current OAuth Client Configuration:**
- **Project**: Your Google Cloud Project
- **Client Type**: Web application
- **Client ID**: `your_oauth_client_id_here`

### **Authorized Redirect URIs:**
```
https://httpsphenikaa-lipidomics-analysis.xyz/auth
https://httpsphenikaa-lipidomics-analysis.xyz/callback
https://httpsphenikaa-lipidomics-analysis.xyz/google
https://httpsphenikaa-lipidomics-analysis.xyz/oauth2
https://httpsphenikaa-lipidomics-analysis.xyz/login/callback
```

### **Authorized JavaScript Origins:**
```
https://httpsphenikaa-lipidomics-analysis.xyz
```

## 📧 **Email Templates Available**

The system includes professional email templates for:
1. **Email Verification** → `templates/email/email_verification.html`
2. **Password Reset** → `templates/email/password_reset.html`  
3. **Admin Notifications** → `templates/email/schedule_admin_notification.html`
4. **User Confirmations** → `templates/email/schedule_user_confirmation.html`
5. **Test Emails** → `templates/email/test_email.html`

## 🎨 **Email Design Features**
- **Phenikaa University Branding** → Official colors and styling
- **Responsive Design** → Mobile-friendly emails
- **Professional Layout** → Clean, modern appearance
- **Action Buttons** → Clear call-to-action elements
- **Security Information** → Professional security notices

## 🛠️ **Troubleshooting**

### **Email Not Sending:**
1. Check Gmail app password is correct
2. Verify SMTP settings in Railway
3. Test with `/test-email` route
4. Check `/email-status` for diagnostics

### **OAuth Not Working:**
1. Verify Google Client ID/Secret in Railway
2. Check redirect URIs in Google Console  
3. Ensure domain matches exactly
4. Test with `/oauth-debug` route

### **Database Issues:**
1. Check `DATABASE_URL` is correct
2. Test with `/api/database-view`
3. Verify PostgreSQL connection

## 🎯 **Expected Results**

After successful configuration, you should see:
- ✅ **Registration emails** sent automatically
- ✅ **Password reset emails** working
- ✅ **Consultation notifications** to admin
- ✅ **User confirmations** for scheduling
- ✅ **Google OAuth** login functional
- ✅ **Demo login** for quick testing
- ✅ **Admin panel** accessible with email tools

## 🔄 **Next Steps After Testing**

1. **Customize email content** for your organization
2. **Scale email delivery** with additional SMTP providers if needed
3. **Configure custom domain** for professional appearance
4. **Add more OAuth providers** if needed
5. **Implement user role management** features

---

**📞 Support**: If you encounter issues, check the `/auth-debug` and `/oauth-debug` routes for detailed troubleshooting information.