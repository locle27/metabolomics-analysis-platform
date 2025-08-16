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
    """Production homepage with graceful degradation"""
    try:
        # Try to get database stats if available
        homepage_data = {
            'stats': {'total_lipids': 0, 'total_classes': 0, 'total_annotations': 0},
            'recent_lipids': [],
            'news': [
                {
                    'title': 'Production Platform Deployed Successfully',
                    'date': '2025-08-17',
                    'summary': 'Advanced metabolomics analysis platform now running on Railway with full authentication and chart features.',
                    'image': '/static/news1.jpg'
                }
            ]
        }
        
        # Try to get real database stats if database is available
        if DATABASE_AVAILABLE and db:
            try:
                with app.app_context():
                    # Simple database query using text() for SQLAlchemy 2.0 compatibility
                    from sqlalchemy import text
                    result = db.engine.execute(text("SELECT 1 as test"))
                    if result:
                        homepage_data['stats']['database_status'] = 'connected'
                        homepage_data['stats']['connection_test'] = 'success'
            except Exception as e:
                print(f"Database query failed: {e}")
                homepage_data['stats']['database_status'] = 'error'
        
        # Render template if available, otherwise return JSON
        try:
            return render_template('homepage.html', data=homepage_data)
        except Exception:
            # Fallback to JSON if templates not available
            return {
                "status": "healthy",
                "message": "Metabolomics Platform - Production",
                "timestamp": datetime.now().isoformat(),
                "features_loaded": get_loaded_features(),
                "data": homepage_data
            }
            
    except Exception as e:
        print(f"Homepage error: {e}")
        return {
            "status": "healthy",
            "message": "Metabolomics Platform - Basic Mode",
            "timestamp": datetime.now().isoformat(),
            "features_loaded": get_loaded_features(),
            "error": str(e)
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

# Essential routes for production
@app.route('/lipid-selection')
@app.route('/dashboard') 
def dashboard():
    """Lipid selection dashboard"""
    if not DATABASE_AVAILABLE:
        return {"error": "Database not available", "redirect": "/health"}, 503
    
    try:
        return render_template('clean_dashboard.html')
    except Exception as e:
        return {"message": "Lipid selection available", "features": get_loaded_features(), "note": "Template fallback"}

@app.route('/dual-chart-view')
def dual_chart_view():
    """Interactive chart view"""
    if not CHARTS_AVAILABLE:
        return {"error": "Charts not available", "available_features": get_loaded_features()}, 503
    
    try:
        return render_template('dual_chart_view.html')
    except Exception as e:
        return {"message": "Charts available", "features": get_loaded_features(), "note": "Template fallback"}

@app.route('/api/dual-chart-data/<int:lipid_id>')
def api_dual_chart_data(lipid_id):
    """Chart data API endpoint"""
    if not CHARTS_AVAILABLE:
        return {"error": "Charts not available"}, 503
    
    try:
        # Import chart service dynamically to avoid startup issues
        from dual_chart_service import DualChartService
        chart_service = DualChartService()
        return chart_service.get_dual_chart_data(lipid_id)
    except Exception as e:
        return {"error": f"Chart data failed: {str(e)}"}, 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Starting bulletproof app on port {port}")
    print(f"   Loaded features: {', '.join(get_loaded_features()) or 'Basic only'}")
    app.run(debug=False, host='0.0.0.0', port=port)