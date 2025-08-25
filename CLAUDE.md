# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Professional Metabolomics Data Analysis Platform** - A Flask-based web application for analyzing lipid chromatography data from the Baker Institute. Features interactive dual-chart visualizations, PostgreSQL database with 822+ lipids, and Phenikaa University-inspired interface.

**Production URL**: https://www.httpsphenikaa-lipidomics-analysis.xyz/

## 🔥 Critical System Information

### **Environment & Commands**
- **OS**: Ubuntu WSL (Windows Subsystem for Linux)  
- **Python**: Always use `python3` (never `python`)
- **Database**: PostgreSQL on Railway cloud (NOT SQLite)
- **Local Dev**: `python3 app.py` → http://localhost:5000

### **Common Commands**
```bash
# Run application
python3 app.py

# Install dependencies
pip install -r requirements.txt

# Database initialization (if needed)
python3 init_database.py

# Git operations
git add -A && git commit -m "message"
```

## 🏗️ System Architecture

### **Database Layer**
- **PostgreSQL** on Railway cloud platform
- **Tables**: `main_lipids` (822+ lipids), `annotated_ions`, `users`, `consultations`
- **Performance**: N+1 problem SOLVED with eager loading (100x faster)
- **Key Optimization**: `joinedload()` and `selectinload()` for efficient queries

### **Core Application Files**
- **`app.py`** - Main Flask application with all routes
- **`models.py`** - SQLAlchemy models (PostgreSQL optimized)
- **`dual_chart_service.py`** - Interactive chart generation
- **`streamlined_calculator_service.py`** - Ratio calculations with numerical sorting

### **Frontend Features**
- **Chart.js 4.4.0** with zoom plugin
- **Dual-chart system**: Chart 1 (focused) + Chart 2 (overview)
- **2D Area-based hover detection** for integration areas
- **Phenikaa University design** with exact colors and layout

## ⚠️ Critical Rules - NEVER VIOLATE

1. **Always use `python3`** - This is Ubuntu, not Windows
2. **Database is PostgreSQL** - Use proper PostgreSQL syntax, not SQLite
3. **Chart 1 shows ONLY main lipid** - No isotopes or Similar MRM
4. **Y-axis compression** - Data must appear close to 0, not proportional
5. **Fixed colors**: Similar MRM = light green (#2ed573), isotope = light red (#ff4757)
6. **Static tooltips** - Only show on colored integration areas

## 🚨 Common Issues & Solutions

### **1. User Management Shows "0 users"**
- **Cause**: Session not authenticated with admin role
- **Fix**: 
  ```
  1. Visit: /fix-admin-session
  2. Then go to: /manage-users
  ```
- **Admin account**: `loc22100302@gmail.com`

### **2. Column Sorting Error (PH-HC samples)**
- **Issue**: PH-HC_1, PH-HC_10, PH-HC_100 instead of PH-HC_1, PH-HC_2, PH-HC_3
- **Fixed in**: `streamlined_calculator_service.py` with numerical sorting

### **3. Missing API Routes (404 errors)**
- **Routes restored**: `/api/load-lipids`, `/api/zoom-settings`, `/api/dual-chart-data`
- **User management**: `/update-user-notifications`, `/bulk-user-actions`

### **4. Railway Health Check Failures**
- **Solution**: Simple CSRF error handler (no session/redirect operations)
- **Health endpoints**: `/health`, `/ping`, `/healthz` exempt from CSRF

### **5. Avatar Display Issues**
- **Fixed**: Shows user initials when images fail
- **Template**: `manage_users.html` with proper onerror handlers

## 📊 Key Features

### **Interactive Dual Charts**
- **Chart 1**: Focused view (RT ± 0.6 minutes)
- **Chart 2**: Full overview (0-16 minutes)
- **Interaction**: Click chart to activate zoom, click outside to deactivate
- **Tooltips**: External info panel (no overlapping tooltips)

### **User Management System**
- **Roles**: admin, manager, user
- **Authentication**: Session-based with OAuth support
- **Database**: 5 existing users including admins

### **Streamlined Calculator**
- **Purpose**: Calculate lipid ratios and percentages
- **Excel Support**: Uploads and processes .xlsx files
- **Numerical Sorting**: Handles PH-HC sample columns correctly

## 🔧 Development Tips

### **Database Operations**
```python
# Always use eager loading for performance
lipids = MainLipid.query.options(
    joinedload(MainLipid.annotated_ions)
).all()
```

### **Session Management**
```python
# Check admin access
if session.get('user_role') != 'admin':
    return redirect(url_for('homepage'))
```

### **Error Handling**
- Always provide fallback for database failures
- Show demo data when database unavailable
- Use try/except blocks with specific error messages

## 📦 Dependencies

**Core**: Flask 2.3.3, SQLAlchemy 2.0.21, psycopg2-binary 2.9.7
**Frontend**: Bootstrap 5, Chart.js 4.4.0, FontAwesome 6
**Analysis**: pandas 2.1.0, numpy 1.26.0, openpyxl 3.1.2

## 🚀 Deployment

**Railway (Production)**:
- Database URL set automatically
- Health checks configured in `railway.json`
- CSRF protection with proper exemptions

**Local Development**:
1. Copy `.env.example` to `.env`
2. Set `DATABASE_URL` to Railway PostgreSQL
3. Run: `python3 app.py`