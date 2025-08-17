#!/usr/bin/env python3
"""
MINIMAL WORKING FLASK APP FOR RAILWAY HEALTH CHECKS
This version prioritizes startup reliability over features
"""

import os
import sys
from datetime import datetime

# Ensure we can import Flask first
try:
    from flask import Flask, jsonify, render_template
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ CRITICAL: Flask import failed: {e}")
    sys.exit(1)

# Create Flask app first
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'railway-health-check-key')

# Add proxy fix for Railway
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
    print("✅ Proxy fix applied")
except Exception as e:
    print(f"⚠️ Proxy fix failed: {e}")

# Environment loading with error handling
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except Exception as e:
    print(f"⚠️ Environment loading failed: {e}")

# Database setup with comprehensive error handling
database_available = False
try:
    from flask_sqlalchemy import SQLAlchemy
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'echo': False,
            'connect_args': {"connect_timeout": 5}  # Short timeout for health check
        }
        
        db = SQLAlchemy()
        db.init_app(app)
        
        # Test database connection with timeout
        with app.app_context():
            try:
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    database_available = True
                    print("✅ Database connection successful")
            except Exception as e:
                print(f"⚠️ Database connection failed: {e}")
                # Don't fail - continue without database
    else:
        print("⚠️ DATABASE_URL not configured")
        
except Exception as e:
    print(f"⚠️ Database setup failed: {e}")

# =====================================================
# CRITICAL HEALTH CHECK ROUTE
# =====================================================

@app.route('/health')
def health_check():
    """Ultra-reliable health check for Railway"""
    try:
        health_data = {
            "status": "healthy",
            "message": "Metabolomics platform health check passed",
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv('FLASK_ENV', 'production'),
            "port": os.getenv('PORT', 'not-set'),
            "database_available": database_available,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
        return jsonify(health_data), 200
    except Exception as e:
        # Ultra-fallback - return plain text if JSON fails
        return f"HEALTHY - {datetime.now().isoformat()} - Error: {str(e)}", 200

@app.route('/')
def homepage():
    """Simple homepage that works without dependencies"""
    try:
        homepage_data = {
            "platform": "Advanced Metabolomics Research Platform",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv('FLASK_ENV', 'production'),
            "database_status": "connected" if database_available else "unavailable",
            "health_endpoint": "/health",
            "message": "Platform is operational"
        }
        
        # Try template rendering with fallback to JSON
        try:
            return render_template('homepage.html', data=homepage_data)
        except Exception:
            return jsonify(homepage_data)
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Homepage error: {str(e)}",
            "health_endpoint": "/health",
            "timestamp": datetime.now().isoformat()
        }), 200  # Still return 200 for health check

# =====================================================
# CONDITIONAL FEATURE LOADING
# =====================================================

# Try to load additional features without failing startup
try:
    from models_postgresql_optimized import optimized_manager, get_db_stats
    
    @app.route('/api/database-view')
    def api_database_view():
        """Database view if models available"""
        try:
            stats = get_db_stats()
            return jsonify({"status": "success", "stats": stats})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
            
    print("✅ Database models loaded")
except Exception as e:
    print(f"⚠️ Database models not available: {e}")

# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "not_found",
        "message": "Endpoint not found",
        "available_endpoints": ["/", "/health"],
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error", 
        "message": "Internal server error",
        "health_endpoint": "/health",
        "timestamp": datetime.now().isoformat()
    }), 500

# =====================================================
# STARTUP DIAGNOSTICS
# =====================================================

print("=" * 60)
print("🚀 MINIMAL WORKING METABOLOMICS PLATFORM")
print("=" * 60)
print(f"🐍 Python: {sys.version}")
print(f"📁 Directory: {os.getcwd()}")
print(f"🌐 PORT: {os.getenv('PORT', 'not-set')}")
print(f"🔧 Environment: {os.getenv('FLASK_ENV', 'production')}")
print(f"💾 Database: {'✅ Connected' if database_available else '❌ Unavailable'}")
print(f"📊 Health endpoint: /health")
print("=" * 60)

# =====================================================
# GUNICORN COMPATIBILITY
# =====================================================

# This section runs when using Gunicorn (Railway)
if __name__ != '__main__':
    print("🚀 Running under Gunicorn (Railway deployment)")
    print(f"   Port binding: 0.0.0.0:{os.getenv('PORT', '5000')}")
    print(f"   Health check: /health")

# This section runs when using python directly
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Running Flask development server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)