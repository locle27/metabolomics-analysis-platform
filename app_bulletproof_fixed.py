#!/usr/bin/env python3
"""
Ultra-Bulletproof Flask App for Railway Production
Handles ALL possible failure scenarios gracefully
"""

import os
import sys
import traceback
from datetime import datetime

# === CRITICAL: Never let the app crash during startup ===
print(f"🚀 Starting bulletproof metabolomics app...")
print(f"🐍 Python: {sys.version}")
print(f"📁 Working directory: {os.getcwd()}")
print(f"🔧 PORT: {os.getenv('PORT', '5000')}")

# Global error tracking
STARTUP_ERRORS = []
AVAILABLE_FEATURES = []

def safe_import(module_name, feature_name):
    """Safely import a module and track success/failure"""
    try:
        if module_name == "flask":
            from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
            AVAILABLE_FEATURES.append(feature_name)
            return True, locals()
        elif module_name == "dotenv":
            from dotenv import load_dotenv
            load_dotenv()
            AVAILABLE_FEATURES.append(feature_name)
            return True, {"load_dotenv": load_dotenv}
        elif module_name == "flask_sqlalchemy":
            from flask_sqlalchemy import SQLAlchemy
            AVAILABLE_FEATURES.append(feature_name)
            return True, {"SQLAlchemy": SQLAlchemy}
        elif module_name == "flask_login":
            from flask_login import LoginManager
            AVAILABLE_FEATURES.append(feature_name)
            return True, {"LoginManager": LoginManager}
        else:
            return False, {}
    except Exception as e:
        STARTUP_ERRORS.append(f"{feature_name}: {str(e)}")
        print(f"⚠️ {feature_name} unavailable: {e}")
        return False, {}

# === Step 1: Core Flask ===
flask_success, flask_modules = safe_import("flask", "flask-core")

if not flask_success:
    # EMERGENCY FALLBACK: Pure Python HTTP server
    print("❌ Flask not available - using emergency HTTP server")
    
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    
    class EmergencyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "emergency_mode",
                "message": "Metabolomics platform in emergency mode - Flask unavailable",
                "timestamp": datetime.now().isoformat(),
                "errors": STARTUP_ERRORS,
                "python_version": sys.version,
                "available_features": AVAILABLE_FEATURES
            }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
    
    try:
        port = int(os.getenv('PORT', 5000))
        server = HTTPServer(('0.0.0.0', port), EmergencyHandler)
        print(f"🚨 EMERGENCY SERVER running on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Emergency server failed: {e}")
        sys.exit(1)

# === Flask is available - continue normal startup ===
Flask = flask_modules["Flask"]
jsonify = flask_modules["jsonify"]
render_template = flask_modules.get("render_template")

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'emergency-fallback-key')

# === Step 2: Environment Variables ===
env_success, env_modules = safe_import("dotenv", "environment")

# === Step 3: Database (Optional) ===
db_success, db_modules = safe_import("flask_sqlalchemy", "database")
db = None

if db_success:
    try:
        SQLAlchemy = db_modules["SQLAlchemy"]
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_pre_ping': True,
                'pool_recycle': 300,
                'echo': False,
                'connect_args': {"connect_timeout": 10}
            }
            
            db = SQLAlchemy()
            db.init_app(app)
            AVAILABLE_FEATURES.append("database-connected")
            print("✅ Database configured")
        else:
            STARTUP_ERRORS.append("No DATABASE_URL found")
            print("⚠️ No DATABASE_URL - database features disabled")
    except Exception as e:
        STARTUP_ERRORS.append(f"Database setup: {str(e)}")
        print(f"⚠️ Database setup failed: {e}")

# === Step 4: Authentication (Optional) ===
auth_success, auth_modules = safe_import("flask_login", "authentication")

if auth_success:
    try:
        LoginManager = auth_modules["LoginManager"]
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        
        # Try to import auth blueprint
        try:
            if os.getenv('FLASK_ENV') == 'production':
                from email_auth_production import auth_bp
            else:
                from email_auth import auth_bp
            app.register_blueprint(auth_bp)
            AVAILABLE_FEATURES.append("authentication-full")
            print("✅ Full authentication loaded")
        except Exception as e:
            STARTUP_ERRORS.append(f"Auth blueprint: {str(e)}")
            print(f"⚠️ Auth blueprint failed: {e}")
            AVAILABLE_FEATURES.append("authentication-basic")
            
    except Exception as e:
        STARTUP_ERRORS.append(f"Authentication: {str(e)}")
        print(f"⚠️ Authentication failed: {e}")

# === Core Routes (Always Available) ===
@app.route('/')
def homepage():
    """Production homepage with comprehensive status"""
    try:
        # Try to get database stats if available
        stats = {"total_lipids": 0, "total_classes": 0, "database_status": "unavailable"}
        recent_lipids = []
        
        if db and "database-connected" in AVAILABLE_FEATURES:
            try:
                with app.app_context():
                    # SQLAlchemy 2.0 compatible queries
                    from sqlalchemy import text
                    with db.engine.connect() as connection:
                        result = connection.execute(text("SELECT 1 as test"))
                        if result:
                            stats["database_status"] = "connected"
                            stats["connection_test"] = "success"
                        
            except Exception as e:
                stats["database_status"] = f"error: {str(e)}"
                STARTUP_ERRORS.append(f"Database query: {str(e)}")
        
        homepage_data = {
            "status": "healthy",
            "message": "Metabolomics Platform - Production Ready",
            "timestamp": datetime.now().isoformat(),
            "features_available": AVAILABLE_FEATURES,
            "startup_errors": STARTUP_ERRORS,
            "stats": stats,
            "recent_lipids": recent_lipids,
            "news": [
                {
                    "title": "Production Platform Successfully Deployed",
                    "date": "2025-08-17",
                    "summary": "Bulletproof deployment with comprehensive error handling and graceful degradation.",
                }
            ]
        }
        
        # Try to render template, fallback to JSON
        if render_template:
            try:
                return render_template('homepage.html', data=homepage_data)
            except Exception as e:
                print(f"Template rendering failed: {e}")
                # Fall through to JSON response
        
        return jsonify(homepage_data)
        
    except Exception as e:
        error_response = {
            "status": "error",
            "message": f"Homepage error: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "features_available": AVAILABLE_FEATURES,
            "startup_errors": STARTUP_ERRORS + [f"Homepage: {str(e)}"]
        }
        return jsonify(error_response), 500

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "features": AVAILABLE_FEATURES,
        "errors": len(STARTUP_ERRORS),
        "database_available": "database-connected" in AVAILABLE_FEATURES,
        "auth_available": any("authentication" in f for f in AVAILABLE_FEATURES),
        "environment": os.getenv('FLASK_ENV', 'production')
    })

@app.route('/status')
def status_page():
    """Detailed status page"""
    return jsonify({
        "platform": "Metabolomics Research Platform",
        "version": "2.0.0-production",
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "available_features": AVAILABLE_FEATURES,
        "startup_errors": STARTUP_ERRORS,
        "environment_variables": {
            "PORT": os.getenv('PORT', 'not set'),
            "FLASK_ENV": os.getenv('FLASK_ENV', 'not set'),
            "DATABASE_URL": "***set***" if os.getenv('DATABASE_URL') else "not set",
            "SECRET_KEY": "***set***" if os.getenv('SECRET_KEY') else "not set"
        },
        "database": {
            "available": "database-connected" in AVAILABLE_FEATURES,
            "url_configured": bool(os.getenv('DATABASE_URL'))
        },
        "authentication": {
            "available": any("authentication" in f for f in AVAILABLE_FEATURES),
            "type": "full" if "authentication-full" in AVAILABLE_FEATURES else "basic" if "authentication-basic" in AVAILABLE_FEATURES else "none"
        }
    })

# === Optional Routes (Only if features available) ===
if "database-connected" in AVAILABLE_FEATURES:
    @app.route('/dashboard')
    def dashboard():
        return jsonify({
            "message": "Dashboard functionality available",
            "features": AVAILABLE_FEATURES,
            "redirect_needed": "Full dashboard requires template rendering"
        })

@app.route('/emergency')
def emergency_info():
    """Emergency information and recovery options"""
    return {
        "emergency_mode": True,
        "message": "Emergency endpoints available for system recovery",
        "available_endpoints": [
            "/health - Health check",
            "/status - Detailed status",
            "/emergency - This page",
            "/ - Homepage (degraded mode)"
        ],
        "recovery_options": [
            "Check environment variables in Railway dashboard",
            "Verify DATABASE_URL is correctly set",
            "Check build logs for dependency installation issues",
            "Contact system administrator"
        ],
        "startup_errors": STARTUP_ERRORS,
        "features": AVAILABLE_FEATURES
    }

# === Error Handlers ===
@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "timestamp": datetime.now().isoformat(),
        "available_features": AVAILABLE_FEATURES,
        "contact": "Check /emergency for recovery options"
    }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "not_found",
        "message": "Endpoint not found",
        "available_endpoints": ["/", "/health", "/status", "/emergency"],
        "timestamp": datetime.now().isoformat()
    }), 404

# === Application Startup ===
if __name__ == '__main__':
    try:
        port = int(os.getenv('PORT', 5000))
        
        print(f"\n🚀 BULLETPROOF METABOLOMICS PLATFORM STARTING")
        print(f"   Port: {port}")
        print(f"   Features loaded: {', '.join(AVAILABLE_FEATURES) or 'Basic only'}")
        if STARTUP_ERRORS:
            print(f"   Startup errors: {len(STARTUP_ERRORS)}")
            for error in STARTUP_ERRORS[:3]:  # Show first 3 errors
                print(f"     - {error}")
        print(f"   Health check: http://localhost:{port}/health")
        print(f"   Status page: http://localhost:{port}/status")
        print(f"   Emergency info: http://localhost:{port}/emergency\n")
        
        app.run(debug=False, host='0.0.0.0', port=port)
        
    except Exception as e:
        print(f"❌ CRITICAL: Failed to start application: {e}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        sys.exit(1)