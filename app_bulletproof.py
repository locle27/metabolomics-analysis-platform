#!/usr/bin/env python3
"""
Bulletproof Flask App - Progressive Loading
Starts with minimal functionality and adds features progressively
"""

import os
import sys
from datetime import datetime

# Step 1: Minimal Flask setup
try:
    from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
    print("✅ Flask imported successfully")
except Exception as e:
    print(f"❌ Flask import failed: {e}")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

# Step 2: Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except Exception as e:
    print(f"⚠️ Environment loading failed: {e}")

# Step 3: Basic routes that always work
@app.route('/')
def homepage():
    """Always working homepage"""
    return {
        "status": "healthy",
        "message": "Metabolomics Platform - Progressive Loading",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv('FLASK_ENV', 'development'),
        "features_loaded": get_loaded_features()
    }

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# Step 4: Try to load database functionality
DATABASE_AVAILABLE = False
db = None

try:
    from flask_sqlalchemy import SQLAlchemy
    
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'echo': False
        }
        
        db = SQLAlchemy()
        db.init_app(app)
        DATABASE_AVAILABLE = True
        print("✅ Database configuration loaded")
    else:
        print("⚠️ No DATABASE_URL found")
        
except Exception as e:
    print(f"⚠️ Database setup failed: {e}")

# Step 5: Try to load authentication
AUTH_AVAILABLE = False

try:
    from flask_login import LoginManager
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Try to import auth blueprint
    if os.getenv('FLASK_ENV') == 'production' or os.getenv('ENV') == 'production':
        from email_auth_production import auth_bp
    else:
        from email_auth import auth_bp
    
    app.register_blueprint(auth_bp)
    AUTH_AVAILABLE = True
    print("✅ Authentication system loaded")
    
except Exception as e:
    print(f"⚠️ Authentication setup failed: {e}")

# Step 6: Try to load chart services
CHARTS_AVAILABLE = False

try:
    from dual_chart_service import DualChartService
    CHARTS_AVAILABLE = True
    print("✅ Chart services loaded")
except Exception as e:
    print(f"⚠️ Chart services failed: {e}")

# Helper function
def get_loaded_features():
    """Return list of successfully loaded features"""
    features = []
    if DATABASE_AVAILABLE:
        features.append("database")
    if AUTH_AVAILABLE:
        features.append("authentication")
    if CHARTS_AVAILABLE:
        features.append("charts")
    return features

# Dashboard route with graceful degradation
@app.route('/dashboard')
def dashboard():
    """Dashboard with feature detection"""
    if not AUTH_AVAILABLE:
        return {"error": "Authentication not available", "available_features": get_loaded_features()}, 503
    
    # Continue with dashboard logic...
    return {"message": "Dashboard available", "features": get_loaded_features()}

# Chart route with graceful degradation
@app.route('/charts')
def charts():
    """Charts with feature detection"""
    if not CHARTS_AVAILABLE:
        return {"error": "Charts not available", "available_features": get_loaded_features()}, 503
    
    return {"message": "Charts available", "features": get_loaded_features()}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Starting bulletproof app on port {port}")
    print(f"   Loaded features: {', '.join(get_loaded_features()) or 'Basic only'}")
    app.run(debug=False, host='0.0.0.0', port=port)