# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Professional Metabolomics Data Analysis Platform** - A Flask-based web application for analyzing lipid chromatography data from the Baker Institute. Features interactive dual-chart visualizations, Excel Generator for LC-MS sequences, Streamlined Calculator with file processing statistics, and PostgreSQL database with 822+ lipids.

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

# Database migrations (when needed)
python3 migrate_calculator_statistics_individual.py
python3 migrate_excel_generator_history.py

# Git operations
git add -A && git commit -m "message"
```

## 🏗️ System Architecture

### **Database Layer**
- **PostgreSQL** on Railway cloud platform
- **Core Tables**: `main_lipids` (822+ lipids), `annotated_ions`, `users`
- **Statistics Tables**: `calculator_statistics` (individual file processing), `excel_generator_history` (configuration history)
- **Performance**: N+1 problem SOLVED with eager loading (100x faster)
- **Key Optimization**: `joinedload()` and `selectinload()` for efficient queries

### **Core Application Files**
- **`app.py`** - Main Flask application (248KB) with all routes and API endpoints
- **`models.py`** - SQLAlchemy models (40KB) with 10+ table definitions
- **`dual_chart_service.py`** - Interactive chart generation for lipid visualization
- **`streamlined_calculator_service.py`** - 3-step metabolomics calculations (Ratio → NIST → Agilent)

### **Frontend Features**
- **Chart.js 4.4.0** with zoom plugin for interactive dual-chart system
- **Always-visible statistics tables** at top of Calculator and Excel Generator pages
- **Configuration history system** with Vietnam timezone (UTC+7) display
- **Professional styling** with Phenikaa University design and consistent UX

## ⚠️ Critical Rules - NEVER VIOLATE

1. **Always use `python3`** - This is Ubuntu, not Windows
2. **Database is PostgreSQL** - Use proper PostgreSQL syntax, not SQLite
3. **Statistics tables are always visible** - Never hide behind user actions
4. **Vietnam time format** - Always UTC+7 in HH:MM:SS format for timestamps
5. **Individual file tracking** - Each file processing creates separate database record
6. **History-based saving** - No global defaults, only user-specific configuration history

## 🚨 Common Issues & Solutions

### **1. Admin Session Issues**
- **Admin account**: `loc22100302@gmail.com` (User ID: 3)
- **Fix session**: Visit `/fix-admin-session` then `/manage-users`
- **Authentication check**: `session.get('user_authenticated')` and `session.get('user_role')`

### **2. Statistics Not Displaying**
- **Cause**: Statistics tables hidden by default or user not authenticated
- **Solution**: Tables should be always visible at page top, show login prompt for anonymous users

### **3. API Route Issues**
- **Active APIs**: `/api/calculator-statistics`, `/api/excel-history`, `/api/dual-chart-data`
- **CSRF Exemptions**: All API endpoints must be in `API_EXEMPT_PATHS` list

## 📊 Key Features

### **Streamlined Calculator**
- **3-Step Process**: Ratio → NIST → Agilent calculations for metabolomics analysis
- **File Processing Statistics**: Always-visible table showing individual file processing history
- **Vietnam Time Display**: All timestamps in UTC+7 HH:MM:SS format
- **Individual Tracking**: Each uploaded file creates separate database record

### **Excel Generator**
- **LC-MS Sequence Generation**: Professional sample sequence generator for lipidomics
- **Configuration History**: Always-visible table with saved configurations and one-click restore
- **Pattern Preview**: Real-time preview of carryover and NIST standard insertion patterns
- **Online Storage**: All configurations saved to PostgreSQL database (survives logout/login)

### **User Management & Authentication**
- **Session-based**: Uses Flask sessions with `user_authenticated`, `user_email`, `user_role`
- **User ID lookup**: Session stores email, app looks up user_id for database operations
- **Anonymous handling**: Statistics tables show login prompts for non-authenticated users

## 🔧 Development Tips

### **Statistics Implementation Pattern**
```python
# Always create individual records (never aggregate)
CalculatorStatistics.add_file_processing(user_id, filename, substance_count)
ExcelGeneratorHistory.add_configuration(user_id, title, inputs)

# User ID lookup from session email
user = User.query.filter_by(email=session.get('user_email')).first()
user_id = user.id if user else None
```

### **Database Operations**
```python
# Use eager loading for performance
lipids = MainLipid.query.options(
    joinedload(MainLipid.annotated_ions)
).all()

# Always handle SQLAlchemy 2.0 compatibility
with db.engine.begin() as connection:
    connection.execute(db.text("SQL QUERY"))
```

### **Frontend Statistics Tables**
- Position: Always at top of page, never hidden
- Login state: Show login prompt for anonymous users
- Auto-refresh: Update tables every 30 seconds and after user actions
- Styling: Consistent gradient headers, hover effects, Vietnam time badges

## 📦 Dependencies & Architecture

**Core**: Flask 2.3.3, SQLAlchemy 2.0.21, psycopg2-binary 2.9.7, pandas 2.1.0
**Frontend**: Bootstrap 5, Chart.js 4.4.0, FontAwesome 6
**Database**: 10+ tables including statistics tracking and history storage

## 🚀 Deployment

**Railway Production**: https://www.httpsphenikaa-lipidomics-analysis.xyz/
- PostgreSQL database with 822+ lipids and statistics tracking
- Health endpoints: `/health`, `/ping`, `/healthz`
- CSRF exemptions for all `/api/*` routes