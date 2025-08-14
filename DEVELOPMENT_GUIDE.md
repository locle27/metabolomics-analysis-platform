# 🚀 DUAL-VERSION DEVELOPMENT GUIDE

## 📋 **SETUP OVERVIEW**

You now have **2 versions** of your metabolomics platform:

### 🧪 **Version 1: LOCAL DEVELOPMENT** 
- **Purpose**: Testing new features, debugging, experimentation
- **Database**: Railway PostgreSQL (same data as production)
- **Environment**: Development mode with debug enabled
- **Location**: Your local machine

### 🌐 **Version 2: RAILWAY PRODUCTION**
- **Purpose**: Official live version for users
- **Database**: Railway PostgreSQL (production data)
- **Environment**: Production mode, optimized for performance
- **Location**: Railway cloud platform

---

## 🧪 **LOCAL DEVELOPMENT VERSION**

### **Quick Start:**
```bash
# Windows PowerShell:
.\venv_linux\Scripts\Activate.ps1
python run_development.py

# WSL/Linux:
source venv_wsl/bin/activate
python run_development.py

# Access: http://localhost:5000
```

### **Features:**
- ✅ **Hot Reload**: Code changes auto-refresh
- ✅ **Debug Mode**: Detailed error messages
- ✅ **Railway Database**: Test with real production data
- ✅ **Safe Testing**: Won't affect production users

### **Environment Configuration:**
- **File**: `.env` (automatically loaded)
- **Database**: Railway PostgreSQL (your imported lipid data)
- **Debug**: Enabled for detailed error tracking
- **Logging**: Verbose for development

---

## 🌐 **RAILWAY PRODUCTION VERSION**

### **Deployment Process:**
```bash
# 1. Test locally first:
python run_development.py
# Verify all features work

# 2. Deploy to Railway:
railway login
railway up
# Or push to connected GitHub repo
```

### **Environment Variables (Set in Railway Dashboard):**
```
DATABASE_URL = postgresql://postgres:VmyAveAhkGVOFlSiVBWgyIEAUbKAXEPi@mainline.proxy.rlwy.net:36647/railway
SECRET_KEY = [Generate secure key - NOT the dev key]
FLASK_ENV = production
FLASK_DEBUG = False
ENVIRONMENT = production
```

### **Features:**
- ✅ **Production Optimized**: Fast performance
- ✅ **Error Handling**: User-friendly error pages
- ✅ **Security**: Production security settings
- ✅ **Monitoring**: Production logging

---

## 🔄 **DEVELOPMENT WORKFLOW**

### **1. Feature Development:**
```bash
# Start development server
python run_development.py

# Make changes to:
# - app.py (routes, logic)
# - templates/*.html (UI)
# - static/* (CSS, JS, images)
# - models.py (database schema)

# Test changes automatically (hot reload)
# Access: http://localhost:5000
```

### **2. Testing with Production Data:**
- ✅ Your development version uses the **same Railway database**
- ✅ Test new features with real lipid data
- ✅ No risk to production users (they use Railway deployment)

### **3. Production Deployment:**
```bash
# After testing locally:
git add .
git commit -m "Add new feature: [description]"
git push origin main

# Railway auto-deploys (if connected to GitHub)
# Or manual deploy: railway up
```

---

## 🛡️ **SAFETY FEATURES**

### **Database Protection:**
- ✅ **Same Database**: Both versions use Railway PostgreSQL
- ✅ **No Conflicts**: Local changes don't affect production until deployed
- ✅ **Backup Available**: Complete backup in `/backup/` folder

### **Code Protection:**
- ✅ **Git Ignore**: `.env` never committed (contains database password)
- ✅ **Separate Configs**: Development vs production settings
- ✅ **Version Control**: Git tracks all code changes

---

## 📁 **FILE STRUCTURE**

```
metabolomics-project/
├── 🧪 DEVELOPMENT FILES
│   ├── .env                    # Local development config (ignored by git)
│   ├── run_development.py      # Development server starter
│   └── venv_wsl/, venv_linux/  # Virtual environments
│
├── 🌐 PRODUCTION FILES  
│   ├── .env.production         # Production config reference
│   ├── run_production.py       # Production server starter (local testing)
│   ├── railway.json           # Railway deployment config
│   ├── runtime.txt            # Python version for Railway
│   └── Procfile              # Railway startup command
│
├── 📁 SHARED FILES
│   ├── app.py                 # Main Flask application
│   ├── models.py              # Database models
│   ├── templates/             # HTML templates
│   ├── static/                # CSS, JS, images
│   └── requirements.txt       # Python dependencies
│
└── 🛡️ SAFETY FILES
    ├── backup/                # Complete project backup
    ├── .gitignore            # Files to never commit
    └── DEVELOPMENT_GUIDE.md   # This guide
```

---

## 🎯 **COMMON COMMANDS**

### **Development:**
```bash
# Start development server
python run_development.py

# Install new package
pip install package-name
pip freeze > requirements.txt

# Database operations
python -c "from models import *; print(f'Lipids: {MainLipid.query.count()}')"
```

### **Production Deployment:**
```bash
# Test production settings locally
python run_production.py

# Deploy to Railway
railway up

# Check Railway logs
railway logs
```

---

## 🚨 **TROUBLESHOOTING**

### **Development Issues:**
- **Database Connection**: Check `.env` file has correct Railway URL
- **Module Errors**: Activate virtual environment first
- **Port Conflicts**: Change port in `run_development.py`

### **Production Issues:**
- **Deployment Fails**: Check Railway logs for errors
- **Database Issues**: Verify environment variables in Railway dashboard
- **Code Conflicts**: Test locally with `run_production.py` first

---

## 🎉 **SUCCESS INDICATORS**

### **Development Version Working:**
- [ ] `python run_development.py` starts without errors
- [ ] Homepage loads at http://localhost:5000
- [ ] Logo displays correctly
- [ ] Dashboard accessible at /dashboard
- [ ] Database shows your imported lipid data

### **Production Version Working:**
- [ ] Railway deployment successful
- [ ] Live URL accessible
- [ ] Same features as development version
- [ ] Production database connection working

---

**🎯 You now have the perfect setup for safe feature development and stable production deployment!**