#!/usr/bin/env python3
"""
ULTIMATE BULLETPROOF FLASK APP FOR RAILWAY DEPLOYMENT
Handles ALL possible failure scenarios and dependency issues
Provides comprehensive debugging and graceful degradation
"""

import os
import sys
import traceback
import json
from datetime import datetime

# === STARTUP LOGGING ===
print("=" * 60)
print("🚀 ULTIMATE BULLETPROOF METABOLOMICS PLATFORM STARTING")
print("=" * 60)
print(f"🐍 Python version: {sys.version}")
print(f"📁 Working directory: {os.getcwd()}")
print(f"🔧 Environment: {os.getenv('FLASK_ENV', 'production')}")
print(f"📡 Port: {os.getenv('PORT', '5000')}")
print(f"⏰ Timestamp: {datetime.now().isoformat()}")
print()

# Global tracking
STARTUP_ERRORS = []
AVAILABLE_FEATURES = []
IMPORT_STATUS = {}

def log_status(message, success=True):
    """Log status with consistent formatting"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def safe_import_with_fallback(module_name, feature_name, fallback_func=None):
    """Safely import with comprehensive error handling and fallbacks"""
    try:
        if module_name == "flask":
            from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
            AVAILABLE_FEATURES.append(feature_name)
            IMPORT_STATUS[module_name] = "success"
            log_status(f"{feature_name} imported successfully")
            return True, {
                "Flask": Flask,
                "jsonify": jsonify,
                "render_template": render_template,
                "request": request,
                "redirect": redirect,
                "url_for": url_for,
                "flash": flash,
                "session": session
            }
        elif module_name == "dotenv":
            from dotenv import load_dotenv
            load_dotenv()
            AVAILABLE_FEATURES.append(feature_name)
            IMPORT_STATUS[module_name] = "success"
            log_status(f"{feature_name} loaded successfully")
            return True, {"load_dotenv": load_dotenv}
        elif module_name == "flask_sqlalchemy":
            from flask_sqlalchemy import SQLAlchemy
            AVAILABLE_FEATURES.append(feature_name)
            IMPORT_STATUS[module_name] = "success"
            log_status(f"{feature_name} imported successfully")
            return True, {"SQLAlchemy": SQLAlchemy}
        elif module_name == "psycopg2":
            import psycopg2
            AVAILABLE_FEATURES.append(feature_name)
            IMPORT_STATUS[module_name] = "success"
            log_status(f"{feature_name} available")
            return True, {"psycopg2": psycopg2}
        elif module_name == "models":
            try:
                from models_postgresql_optimized import db, MainLipid, optimized_manager, get_db_stats
                AVAILABLE_FEATURES.append("postgresql-models")
                IMPORT_STATUS[module_name] = "postgresql"
                log_status("PostgreSQL models imported successfully")
                return True, {
                    "db": db,
                    "MainLipid": MainLipid,
                    "optimized_manager": optimized_manager,
                    "get_db_stats": get_db_stats
                }
            except Exception as e1:
                try:
                    from models_sqlite import fast_db
                    AVAILABLE_FEATURES.append("sqlite-models")
                    IMPORT_STATUS[module_name] = "sqlite"
                    log_status("SQLite models imported as fallback")
                    return True, {"fast_db": fast_db}
                except Exception as e2:
                    raise Exception(f"Neither PostgreSQL ({e1}) nor SQLite ({e2}) models available")
        elif module_name == "chart_services":
            services = {}
            try:
                from dual_chart_service import DualChartService
                services["DualChartService"] = DualChartService
                AVAILABLE_FEATURES.append("dual-charts")
                log_status("Dual chart service loaded")
            except Exception as e:
                log_status(f"Dual chart service failed: {e}", False)
            
            try:
                from simple_chart_service import SimpleChartGenerator
                services["SimpleChartGenerator"] = SimpleChartGenerator
                AVAILABLE_FEATURES.append("simple-charts")
                log_status("Simple chart service loaded")
            except Exception as e:
                log_status(f"Simple chart service failed: {e}", False)
            
            if services:
                IMPORT_STATUS[module_name] = "partial"
                return True, services
            else:
                raise Exception("No chart services available")
                
        elif module_name == "authentication":
            try:
                from flask_login import LoginManager, login_required, current_user
                try:
                    if os.getenv('FLASK_ENV') == 'production':
                        from email_auth_production import auth_bp
                    else:
                        from email_auth import auth_bp
                    AVAILABLE_FEATURES.append("auth-full")
                    IMPORT_STATUS[module_name] = "full"
                    log_status("Full authentication system loaded")
                    return True, {
                        "LoginManager": LoginManager,
                        "login_required": login_required,
                        "current_user": current_user,
                        "auth_bp": auth_bp
                    }
                except Exception as e:
                    AVAILABLE_FEATURES.append("auth-basic")
                    IMPORT_STATUS[module_name] = "basic"
                    log_status(f"Basic authentication only (blueprint failed: {e})")
                    return True, {
                        "LoginManager": LoginManager,
                        "login_required": login_required,
                        "current_user": current_user
                    }
            except Exception as e:
                raise Exception(f"Authentication completely unavailable: {e}")
        else:
            raise Exception(f"Unknown module: {module_name}")
            
    except Exception as e:
        error_msg = f"{feature_name}: {str(e)}"
        STARTUP_ERRORS.append(error_msg)
        IMPORT_STATUS[module_name] = f"failed: {str(e)}"
        log_status(error_msg, False)
        
        # Try fallback if provided
        if fallback_func:
            try:
                fallback_result = fallback_func()
                AVAILABLE_FEATURES.append(f"{feature_name}-fallback")
                log_status(f"{feature_name} fallback activated")
                return True, fallback_result
            except Exception as fe:
                log_status(f"{feature_name} fallback also failed: {fe}", False)
        
        return False, {}

# === STEP 1: FLASK CORE (CRITICAL) ===
print("🔧 Step 1: Loading Flask core...")
flask_success, flask_modules = safe_import_with_fallback("flask", "flask-core")

if not flask_success:
    print("\n🚨 CRITICAL: Flask unavailable - starting emergency HTTP server")
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class EmergencyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            emergency_response = {
                "status": "emergency_mode",
                "message": "Metabolomics platform running in emergency mode - Flask unavailable",
                "timestamp": datetime.now().isoformat(),
                "errors": STARTUP_ERRORS,
                "python_version": sys.version,
                "environment": {
                    "PORT": os.getenv('PORT', 'not set'),
                    "FLASK_ENV": os.getenv('FLASK_ENV', 'not set'),
                    "DATABASE_URL": "configured" if os.getenv('DATABASE_URL') else "not set"
                },
                "available_features": AVAILABLE_FEATURES,
                "import_status": IMPORT_STATUS,
                "recovery_instructions": [
                    "Check that all dependencies are installed in requirements.txt",
                    "Verify Python environment has Flask installed",
                    "Check Railway build logs for installation errors",
                    "Contact system administrator if issues persist"
                ]
            }
            
            self.wfile.write(json.dumps(emergency_response, indent=2).encode())
    
    try:
        port = int(os.getenv('PORT', 5000))
        server = HTTPServer(('0.0.0.0', port), EmergencyHandler)
        print(f"🚨 EMERGENCY HTTP SERVER running on port {port}")
        print(f"🔗 Health check: http://localhost:{port}/")
        server.serve_forever()
    except Exception as e:
        print(f"❌ FATAL: Even emergency server failed: {e}")
        sys.exit(1)

# === FLASK AVAILABLE - CONTINUE SETUP ===
Flask = flask_modules["Flask"]
jsonify = flask_modules["jsonify"]
render_template = flask_modules.get("render_template")
request = flask_modules.get("request")
redirect = flask_modules.get("redirect")
url_for = flask_modules.get("url_for")
flash = flask_modules.get("flash")

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', f'emergency-key-{datetime.now().strftime("%Y%m%d")}')

# === STEP 2: ENVIRONMENT VARIABLES ===
print("\n🔧 Step 2: Loading environment...")
env_success, env_modules = safe_import_with_fallback("dotenv", "environment")

# === STEP 3: DATABASE SETUP ===
print("\n🔧 Step 3: Setting up database...")
database_available = False
db = None

# First check if PostgreSQL driver available
psycopg2_success, psycopg2_modules = safe_import_with_fallback("psycopg2", "postgresql-driver")

# Then try to set up SQLAlchemy
sqlalchemy_success, sqlalchemy_modules = safe_import_with_fallback("flask_sqlalchemy", "sqlalchemy")

if sqlalchemy_success:
    try:
        SQLAlchemy = sqlalchemy_modules["SQLAlchemy"]
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
            
            # Test database connection
            with app.app_context():
                try:
                    from sqlalchemy import text
                    with db.engine.connect() as connection:
                        result = connection.execute(text("SELECT 1 as test"))
                        if result:
                            database_available = True
                            AVAILABLE_FEATURES.append("database-connected")
                            log_status("Database connection successful")
                except Exception as e:
                    STARTUP_ERRORS.append(f"Database connection test failed: {str(e)}")
                    log_status(f"Database connection test failed: {e}", False)
        else:
            STARTUP_ERRORS.append("DATABASE_URL not configured")
            log_status("DATABASE_URL not configured", False)
    except Exception as e:
        STARTUP_ERRORS.append(f"Database setup failed: {str(e)}")
        log_status(f"Database setup failed: {e}", False)

# === STEP 4: MODELS ===
print("\n🔧 Step 4: Loading database models...")
models_success, models_modules = safe_import_with_fallback("models", "database-models")

# === STEP 5: CHART SERVICES ===
print("\n🔧 Step 5: Loading chart services...")
charts_success, chart_modules = safe_import_with_fallback("chart_services", "chart-services")

# === STEP 6: AUTHENTICATION ===
print("\n🔧 Step 6: Setting up authentication...")
auth_success, auth_modules = safe_import_with_fallback("authentication", "authentication")

if auth_success:
    try:
        LoginManager = auth_modules["LoginManager"]
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        
        if "auth_bp" in auth_modules:
            app.register_blueprint(auth_modules["auth_bp"])
            log_status("Authentication blueprint registered")
    except Exception as e:
        STARTUP_ERRORS.append(f"Authentication setup failed: {str(e)}")
        log_status(f"Authentication setup failed: {e}", False)

# === CORE ROUTES ===
print("\n🔧 Step 7: Registering routes...")

@app.route('/')
def homepage():
    """Production homepage with comprehensive system status"""
    try:
        # Database stats
        stats = {"total_lipids": 0, "total_classes": 0, "database_status": "unavailable"}
        recent_lipids = []
        
        if database_available and models_success and "get_db_stats" in models_modules:
            try:
                get_db_stats = models_modules["get_db_stats"]
                stats = get_db_stats()
                stats["database_status"] = "connected"
                
                if "optimized_manager" in models_modules:
                    optimized_manager = models_modules["optimized_manager"]
                    recent_lipids = optimized_manager.get_lipids_sample(3)
            except Exception as e:
                stats["database_status"] = f"error: {str(e)}"
                STARTUP_ERRORS.append(f"Database query error: {str(e)}")
        
        homepage_data = {
            "status": "healthy",
            "platform": "Advanced Metabolomics Research Platform",
            "version": "3.0.0-bulletproof",
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv('FLASK_ENV', 'production'),
            "features_available": AVAILABLE_FEATURES,
            "startup_errors": STARTUP_ERRORS,
            "import_status": IMPORT_STATUS,
            "stats": stats,
            "recent_lipids": recent_lipids,
            "news": [
                {
                    "title": "Bulletproof Deployment System Active",
                    "date": "2025-08-17",
                    "summary": "Ultra-reliable deployment with comprehensive error handling and graceful degradation.",
                },
                {
                    "title": "Advanced Error Recovery Implemented",
                    "date": "2025-08-17", 
                    "summary": "System can handle any import failure or dependency issue while maintaining core functionality.",
                }
            ],
            "system_info": {
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "port": os.getenv('PORT', '5000'),
                "database_available": database_available,
                "authentication_available": auth_success,
                "charts_available": charts_success,
                "models_available": models_success
            }
        }
        
        # Try template rendering with fallback to JSON
        if render_template and "flask-core" in AVAILABLE_FEATURES:
            try:
                return render_template('homepage.html', data=homepage_data)
            except Exception as e:
                log_status(f"Template rendering failed: {e}", False)
                # Fall through to JSON response
        
        return jsonify(homepage_data)
        
    except Exception as e:
        error_response = {
            "status": "error",
            "message": f"Homepage error: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc(),
            "features_available": AVAILABLE_FEATURES,
            "startup_errors": STARTUP_ERRORS + [f"Homepage: {str(e)}"],
            "recovery_endpoint": "/emergency"
        }
        return jsonify(error_response), 500

@app.route('/health')
def health_check():
    """Railway health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv('FLASK_ENV', 'production'),
        "features": AVAILABLE_FEATURES,
        "error_count": len(STARTUP_ERRORS),
        "database_available": database_available,
        "auth_available": auth_success,
        "charts_available": charts_success,
        "import_status": IMPORT_STATUS,
        "python_version": sys.version_info[:2]
    })

@app.route('/status')
def detailed_status():
    """Comprehensive system status"""
    return jsonify({
        "platform": "Advanced Metabolomics Research Platform",
        "version": "3.0.0-bulletproof",
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "available_features": AVAILABLE_FEATURES,
        "startup_errors": STARTUP_ERRORS,
        "import_status": IMPORT_STATUS,
        "environment_variables": {
            "PORT": os.getenv('PORT', 'not set'),
            "FLASK_ENV": os.getenv('FLASK_ENV', 'not set'),
            "DATABASE_URL": "configured" if os.getenv('DATABASE_URL') else "not set",
            "SECRET_KEY": "configured" if os.getenv('SECRET_KEY') else "not set"
        },
        "system_status": {
            "database_available": database_available,
            "authentication_available": auth_success,
            "charts_available": charts_success,
            "models_available": models_success,
            "templates_available": render_template is not None
        },
        "recovery_options": [
            "/emergency - Emergency information",
            "/health - Health check",
            "/status - This status page",
            "/ - Homepage (may work in degraded mode)"
        ]
    })

@app.route('/emergency')
def emergency_info():
    """Emergency recovery information"""
    return jsonify({
        "emergency_mode": True,
        "message": "Emergency diagnostics and recovery information",
        "timestamp": datetime.now().isoformat(),
        "critical_status": {
            "flask_working": "flask-core" in AVAILABLE_FEATURES,
            "database_working": database_available,
            "environment_loaded": "environment" in AVAILABLE_FEATURES
        },
        "startup_errors": STARTUP_ERRORS,
        "import_status": IMPORT_STATUS,
        "available_endpoints": [
            "/ - Homepage",
            "/health - Health check", 
            "/status - Detailed status",
            "/emergency - This page"
        ],
        "recovery_steps": [
            "1. Check Railway dashboard for environment variables",
            "2. Verify DATABASE_URL is correctly configured",
            "3. Check build logs for dependency installation issues",
            "4. Ensure all packages in requirements.txt are installing",
            "5. Verify Python version compatibility",
            "6. Check for Railway service limits or quotas"
        ],
        "debug_info": {
            "python_executable": sys.executable,
            "python_path": sys.path[:3],  # First 3 paths only
            "environment_vars_count": len([k for k in os.environ.keys() if not k.startswith('_')]),
            "working_directory": os.getcwd(),
            "current_time": datetime.now().isoformat()
        }
    })

# === CONDITIONAL ROUTES (ONLY IF FEATURES AVAILABLE) ===
if database_available and models_success:
    @app.route('/dashboard')
    @app.route('/lipid-selection')
    def dashboard():
        """Lipid selection dashboard"""
        try:
            if render_template:
                return render_template('clean_dashboard.html', data={
                    'stats': {},
                    'lipids': [],
                    'classes': [],
                    'query_time': '0.000s',
                    'lazy_loading': True
                })
            else:
                return jsonify({
                    "message": "Dashboard available but template rendering disabled",
                    "redirect_to": "/api/database-view"
                })
        except Exception as e:
            return jsonify({"error": f"Dashboard error: {str(e)}"}), 500

    @app.route('/api/database-view')
    def api_database_view():
        """Database view API"""
        try:
            if "get_db_stats" in models_modules:
                get_db_stats = models_modules["get_db_stats"]
                stats = get_db_stats()
            else:
                stats = {"message": "Database stats unavailable"}
            
            return jsonify({
                "status": "success",
                "stats": stats,
                "features": AVAILABLE_FEATURES
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if charts_success:
    @app.route('/dual-chart-view')
    def dual_chart_view():
        """Interactive chart view"""
        try:
            if render_template:
                return render_template('dual_chart_view.html')
            else:
                return jsonify({"message": "Charts available but template rendering disabled"})
        except Exception as e:
            return jsonify({"error": f"Chart view error: {str(e)}"}), 500

# === ERROR HANDLERS ===
@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "timestamp": datetime.now().isoformat(),
        "available_features": AVAILABLE_FEATURES,
        "recovery_endpoint": "/emergency"
    }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "not_found",
        "message": "Endpoint not found",
        "available_endpoints": ["/", "/health", "/status", "/emergency"],
        "timestamp": datetime.now().isoformat()
    }), 404

# === APPLICATION STARTUP ===
if __name__ == '__main__':
    try:
        port = int(os.getenv('PORT', 5000))
        
        print("\n" + "=" * 60)
        print("🚀 BULLETPROOF METABOLOMICS PLATFORM READY")
        print("=" * 60)
        print(f"🌐 Port: {port}")
        print(f"🎯 Environment: {os.getenv('FLASK_ENV', 'production')}")
        print(f"✨ Features loaded: {len(AVAILABLE_FEATURES)}")
        for feature in AVAILABLE_FEATURES:
            print(f"   ✅ {feature}")
        
        if STARTUP_ERRORS:
            print(f"⚠️  Startup errors: {len(STARTUP_ERRORS)}")
            for i, error in enumerate(STARTUP_ERRORS[:5], 1):  # Show first 5
                print(f"   {i}. {error}")
            if len(STARTUP_ERRORS) > 5:
                print(f"   ... and {len(STARTUP_ERRORS) - 5} more")
        
        print(f"\n🔗 Health check: http://localhost:{port}/health")
        print(f"📊 Status page: http://localhost:{port}/status")
        print(f"🚨 Emergency info: http://localhost:{port}/emergency")
        print(f"🏠 Homepage: http://localhost:{port}/")
        print("=" * 60)
        
        app.run(debug=False, host='0.0.0.0', port=port)
        
    except Exception as e:
        print(f"\n❌ FATAL: Application startup failed: {e}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print("\n🆘 EMERGENCY: Check the following:")
        print("   1. Is the PORT environment variable set correctly?")
        print("   2. Are all required dependencies installed?")
        print("   3. Is there a port conflict with another service?")
        print("   4. Check Railway logs for more detailed error information")
        sys.exit(1)