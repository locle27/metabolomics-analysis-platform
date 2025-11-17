# Railway Free Tier Setup Guide

## 🚀 Migration from Hobby to Free Tier

This guide helps you migrate the Metabolomics Analysis Platform from Railway Hobby tier to the **Free Tier** with local username/password authentication (OAuth removed).

---

## ✅ Changes Made

### 1. **Authentication System Updated**
- ❌ **Removed**: Google OAuth login (requires verified domain on free tier)
- ✅ **Added**: Local username/password authentication
- ✅ All user passwords reset to `1` for easy access

### 2. **Login Credentials**

All 8 users can now login with:
- **Username/Email**: Their registered email or username
- **Password**: `1`

**User List:**
```
Username: admin                    Email: admin@phenikaa.edu.vn                 Password: 1
Username: testuser                 Email: loc22100302@gmail.com                 Password: 1
Username: loc12312301              Email: loc2207nt8.10@gmail.com               Password: 1
Username: hungle2210123            Email: hungle2210123@gmail.com               Password: 1
Username: 23011074                 Email: 23011074@st.phenikaa-uni.edu.vn       Password: 1
Username: minh.phamdang            Email: minh.phamdang@phenikaa-uni.edu.vn     Password: 1
Username: linh.nguyennhat          Email: linh.nguyennhat@phenikaa-uni.edu.vn   Password: 1
Username: adwaith.charvik          Email: adwaith.charvik@gmail.com             Password: 1
```

### 3. **UI Changes**
- Removed "Đăng nhập với Google" button from login page
- Simplified login form to username/password only
- Registration still available at `/auth/register`

---

## 🔧 Railway Free Tier Configuration

### **Environment Variables to Set on Railway:**

1. **Database** (PostgreSQL plugin):
   ```
   DATABASE_URL=<automatically set by Railway>
   ```

2. **Security**:
   ```
   SECRET_KEY=<generate a random 32+ character string>
   ```
   Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

3. **Environment**:
   ```
   ENVIRONMENT=production
   FLASK_ENV=production
   FLASK_DEBUG=False
   ```

4. **OAuth - DISABLED** (comment out or remove):
   ```
   # GOOGLE_CLIENT_ID=
   # GOOGLE_CLIENT_SECRET=
   ```

5. **Optional - Demo Mode**:
   ```
   DEMO_ENABLED=true
   PROD_USE_DEMO_LOGIN=true
   ```

---

## 📦 Railway Free Tier Limits

| Resource | Free Tier Limit |
|----------|-----------------|
| **Execution time** | 500 hours/month |
| **RAM** | 512 MB |
| **Deployments** | Unlimited |
| **Builds** | 100 builds/month |
| **Custom domains** | ❌ Not available (use Railway subdomain) |
| **PostgreSQL** | 1 GB storage (plugin) |

**Important Notes:**
- Free tier uses `*.up.railway.app` subdomain
- Custom domains require Hobby plan ($5/month)
- OAuth with Google requires verified domain (not available on free tier)
- Sleep after 1 hour of inactivity (wakes on first request)

---

## 🚂 Deployment Steps

### **Step 1: Connect to Railway**

1. Go to [railway.app](https://railway.app)
2. Login with GitHub account
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select: `locle27/metabolomics-analysis-platform`

### **Step 2: Add PostgreSQL Database**

1. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway will automatically set `DATABASE_URL` environment variable
3. Copy the connection string for reference

### **Step 3: Set Environment Variables**

Click on your service → **"Variables"** tab → Add:

```bash
# Core Settings
SECRET_KEY=<generate random 32+ char string>
ENVIRONMENT=production
FLASK_ENV=production
FLASK_DEBUG=False

# Demo Mode (optional)
DEMO_ENABLED=true
PROD_USE_DEMO_LOGIN=true

# OAuth DISABLED (no custom domain on free tier)
# GOOGLE_CLIENT_ID=
# GOOGLE_CLIENT_SECRET=
```

### **Step 4: Deploy**

1. Click **"Deploy"** on Railway dashboard
2. Wait for build to complete (~5-10 minutes)
3. Railway will assign a URL: `https://<your-project>.up.railway.app`

### **Step 5: Initialize Database**

Once deployed, run migrations:
```bash
railway run python3 migrate_calculator_statistics_individual.py
railway run python3 migrate_excel_generator_history.py
```

Or use Railway CLI:
```bash
railway link
railway run bash
# Inside container:
python3 reset_all_passwords.py  # Ensure all passwords are '1'
```

### **Step 6: Verify Login**

1. Visit: `https://<your-project>.up.railway.app`
2. Click **"Đăng Nhập"**
3. Login with:
   - Email: `admin@phenikaa.edu.vn`
   - Password: `1`

---

## 🔐 Security Recommendations

### **After Deployment, Update Passwords:**

1. Login with password `1`
2. Go to user profile/settings
3. Change password to something secure
4. Share new credentials with users

### **Or Reset Specific User Password:**

```python
from app import app, db
from models import User

with app.app_context():
    user = User.query.filter_by(email='admin@phenikaa.edu.vn').first()
    user.set_password('new_secure_password')
    db.session.commit()
    print(f"✅ Password updated for {user.email}")
```

---

## 🐛 Troubleshooting

### **Issue: "OAuth service is not available"**
✅ **Fixed**: OAuth has been removed. Use username/password login.

### **Issue: "Database connection failed"**
1. Check Railway PostgreSQL plugin is running
2. Verify `DATABASE_URL` environment variable is set
3. Check logs: `railway logs`

### **Issue: "Invalid credentials"**
1. Make sure you ran `reset_all_passwords.py`
2. Try email instead of username (or vice versa)
3. Password is exactly `1` (no quotes, no spaces)

### **Issue: "Application not starting"**
1. Check logs: `railway logs --lines 100`
2. Verify all required environment variables are set
3. Check `requirements.txt` is up to date

### **Issue: "Out of memory"**
Free tier has 512 MB RAM limit:
1. Optimize imports (use lazy loading)
2. Reduce concurrent workers
3. Consider upgrading to Hobby tier ($5/month)

---

## 📊 Monitoring Free Tier Usage

### **Check Usage Dashboard:**
1. Go to Railway dashboard
2. Click **"Usage"** tab
3. Monitor:
   - Execution hours: <500 hours/month
   - Builds: <100 builds/month
   - Database storage: <1 GB

### **Optimize for Free Tier:**
- **Enable sleep mode**: App sleeps after 1 hour inactivity (auto-wakes)
- **Minimize builds**: Only push when necessary
- **Database cleanup**: Regular cleanup of old data

---

## 🔄 Upgrade Path

If you need custom domain or more resources:

### **Hobby Tier ($5/month):**
- ✅ Custom domains
- ✅ 8 GB RAM
- ✅ No sleep mode
- ✅ 500 hours → **500 hours/month** (same)
- ✅ Can re-enable OAuth with custom domain

### **To Upgrade:**
1. Railway dashboard → **"Settings"** → **"Upgrade to Hobby"**
2. Add custom domain in **"Domains"** tab
3. Re-enable OAuth by uncommenting `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
4. Re-add Google OAuth button in login template

---

## 📝 File Changes Summary

### **Modified Files:**
1. ✅ `templates/auth/login.html` - Removed Google OAuth button
2. ✅ `.env` - Disabled OAuth credentials
3. ✅ `reset_all_passwords.py` - Script to reset all passwords to '1'

### **Files to Deploy:**
- All existing files
- New: `reset_all_passwords.py`
- New: `RAILWAY_FREE_TIER_SETUP.md` (this file)

---

## ✨ Summary

**What Changed:**
- ❌ No more Google OAuth (requires custom domain)
- ✅ Simple username/password login
- ✅ All passwords reset to `1`
- ✅ Free tier compatible

**What Works:**
- ✅ All metabolomics calculations
- ✅ Streamlined Calculator
- ✅ Excel Generator
- ✅ Dual Chart Visualizations
- ✅ User authentication (local)
- ✅ PostgreSQL database
- ✅ File uploads and downloads

**What Doesn't Work:**
- ❌ Google OAuth login (requires Hobby tier + custom domain)
- ❌ Custom domain (requires Hobby tier)

**Next Steps:**
1. Deploy to Railway free tier
2. Test login with password `1`
3. Update user passwords to secure values
4. Monitor usage to stay within free tier limits

---

## 🆘 Support

**Issues or Questions:**
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project GitHub: https://github.com/locle27/metabolomics-analysis-platform

**Created:** 2025-01-17
**Updated:** 2025-01-17
**Version:** 1.0.0
