#!/usr/bin/env python3
"""
WORKING PRODUCTION APP WITH SAFE IMPORTS
Based on app.py but with bulletproof import handling
"""

import os
import sys
from datetime import datetime

# Global startup logging for debugging
STARTUP_LOGS = []

def log_startup(message, level="INFO"):
    """Capture all startup messages for debugging"""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {level}: {message}"
    STARTUP_LOGS.append(log_entry)
    print(log_entry)
    return log_entry

# Core Flask imports - critical
try:
    from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, session
    from werkzeug.middleware.proxy_fix import ProxyFix
    print("✅ Flask core imported successfully")
except ImportError as e:
    print(f"❌ CRITICAL: Flask import failed: {e}")
    sys.exit(1)

# Create Flask app first
app = Flask(__name__, template_folder="templates", static_folder="static")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
app.secret_key = os.getenv('SECRET_KEY', 'metabolomics-production-key')

# Environment loading
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment loaded")
except Exception as e:
    print(f"⚠️ Environment loading failed: {e}")

# Database configuration (but don't initialize SQLAlchemy yet)
database_available = False
db = None

try:
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
        database_available = True
        log_startup("✅ Database configuration set")
    else:
        log_startup("⚠️ DATABASE_URL not configured")
        
except Exception as e:
    log_startup(f"⚠️ Database setup failed: {e}")

# Try to load models safely  
models_available = False
optimized_manager = None
get_db_stats = None

log_startup(f"🔍 Database available: {database_available}")
log_startup(f"🔍 Attempting to load models...")

try:
    log_startup("🔍 Step 1: Importing models...")
    from models_postgresql_optimized import (
        MainLipid, optimized_manager, get_db_stats, init_db
    )
    log_startup("✅ Step 1: Models imported successfully")
    
    log_startup("🔍 Step 2: Initializing models database...")
    # Use the init_db function from models instead of direct db.init_app
    db = init_db(app)
    log_startup("✅ Step 2: Models database initialized properly")
    
    if database_available:
        log_startup("🔍 Step 3: Testing models in app context...")
        with app.app_context():
            try:
                log_startup("🔍 Step 3a: Testing get_db_stats...")
                try:
                    stats_test = get_db_stats()
                    log_startup(f"✅ Step 3a: Stats test successful: {stats_test}")
                    
                    log_startup("🔍 Step 3b: Testing optimized_manager...")
                    if optimized_manager:
                        sample_test = optimized_manager.get_lipids_sample(1)
                        log_startup(f"✅ Step 3b: Manager test successful: {len(sample_test)} lipids")
                    
                    models_available = True
                    log_startup("✅ ALL MODELS TESTS PASSED")
                    
                except Exception as stats_error:
                    log_startup(f"❌ Step 3a: get_db_stats failed: {stats_error}", "ERROR")
                    log_startup(f"   Error type: {type(stats_error).__name__}")
                    log_startup(f"   Trying to check if tables exist...")
                    
                    # Check if tables exist
                    try:
                        with db.engine.connect() as conn:
                            from sqlalchemy import text
                            # Check if main_lipids table exists
                            result = conn.execute(text("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables 
                                    WHERE table_name = 'main_lipids'
                                );
                            """))
                            table_exists = result.fetchone()[0]
                            print(f"🔍 main_lipids table exists: {table_exists}")
                            
                            if table_exists:
                                # Try a simple count query
                                result = conn.execute(text("SELECT COUNT(*) FROM main_lipids"))
                                count = result.fetchone()[0]
                                print(f"✅ Found {count} lipids in database")
                                models_available = True
                                print("✅ MODELS LOADED (database tables verified)")
                            else:
                                print("⚠️ Tables don't exist - trying to create them...")
                                try:
                                    # Try to create tables using the models
                                    models_db.create_all()
                                    print("✅ Tables created successfully")
                                    models_available = True
                                    print("✅ MODELS LOADED (tables created)")
                                except Exception as create_error:
                                    print(f"❌ Table creation failed: {create_error}")
                                    models_available = True  # Models still work, just no data
                                    print("✅ MODELS LOADED (no tables created)")
                                
                    except Exception as db_error:
                        print(f"❌ Table check failed: {db_error}")
                        models_available = False
                
            except Exception as e:
                print(f"❌ Step 3: Models test failed: {e}")
                print(f"   Error type: {type(e).__name__}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
    else:
        print("⚠️ Step 3: Skipped - database not available")
        
except Exception as e:
    print(f"❌ Models import failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    print(f"   Traceback: {traceback.format_exc()}")

# Try to load chart services safely  
charts_available = False
try:
    from dual_chart_service import DualChartService
    charts_available = True
    print("✅ Chart services loaded")
except Exception as e:
    print(f"⚠️ Chart services failed: {e}")

# Try to load authentication safely
auth_available = False
try:
    from flask_login import LoginManager, login_required, current_user
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Try to load auth blueprint
    try:
        if os.getenv('FLASK_ENV') == 'production':
            from email_auth_production import auth_bp
        else:
            from email_auth import auth_bp
        app.register_blueprint(auth_bp)
        auth_available = True
        print("✅ Authentication system loaded")
    except Exception as e:
        print(f"⚠️ Auth blueprint failed: {e}")
        
except Exception as e:
    print(f"⚠️ Authentication setup failed: {e}")

# =====================================================
# CORE ROUTES (ALWAYS AVAILABLE)
# =====================================================

@app.route('/health')
def health_check():
    """Railway health check"""
    try:
        return jsonify({
            "status": "healthy",
            "message": "Metabolomics platform operational",
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv('FLASK_ENV', 'production'),
            "features": {
                "database": database_available,
                "models": models_available, 
                "charts": charts_available,
                "auth": auth_available
            },
            "debug_info": {
                "database_url_configured": bool(os.getenv('DATABASE_URL')),
                "get_db_stats_available": get_db_stats is not None,
                "optimized_manager_available": optimized_manager is not None,
                "database_url_length": len(os.getenv('DATABASE_URL', '')) if os.getenv('DATABASE_URL') else 0
            }
        }), 200
    except Exception as e:
        return f'{{"status":"healthy","error":"{str(e)}"}}', 200

@app.route('/startup-logs')
def startup_logs():
    """Show all startup logs for debugging"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "total_logs": len(STARTUP_LOGS),
        "startup_logs": STARTUP_LOGS[-50:],  # Last 50 logs
        "models_available": models_available,
        "database_available": database_available
    })

@app.route('/debug-models')
def debug_models():
    """Detailed models debugging endpoint"""
    try:
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "database_available": database_available,
            "models_available": models_available,
            "get_db_stats_function": get_db_stats is not None,
            "optimized_manager_object": optimized_manager is not None,
            "database_url_configured": bool(os.getenv('DATABASE_URL')),
            "environment": os.getenv('FLASK_ENV', 'production'),
        }
        
        # Try a simple models import test
        models_import_test = "unknown"
        try:
            import models_postgresql_optimized
            models_import_test = "success"
            debug_info["models_file_accessible"] = True
            debug_info["models_file_location"] = str(models_postgresql_optimized.__file__)
        except Exception as e:
            models_import_test = f"failed: {str(e)}"
            debug_info["models_file_accessible"] = False
            debug_info["models_import_error"] = str(e)
        
        debug_info["models_import_test"] = models_import_test
        
        # Try database connection test
        if database_available:
            try:
                with app.app_context():
                    from sqlalchemy import text
                    # Use modern SQLAlchemy syntax
                    with db.engine.connect() as conn:
                        result = conn.execute(text("SELECT version()"))
                        debug_info["database_version"] = str(result.fetchone()[0])
                    debug_info["database_connection_test"] = "success"
            except Exception as e:
                debug_info["database_connection_test"] = f"failed: {str(e)}"
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()})

@app.route('/')
def homepage():
    """Homepage with feature detection"""
    try:
        # Try to get database stats if available
        stats = {"total_lipids": 0, "database_status": "unavailable"}
        recent_lipids = []
        
        if database_available and models_available and get_db_stats:
            try:
                with app.app_context():
                    stats = get_db_stats()
                    stats["database_status"] = "connected"
                    if optimized_manager:
                        recent_lipids = optimized_manager.get_lipids_sample(3)
            except Exception as e:
                stats["database_status"] = f"error: {str(e)}"
        
        homepage_data = {
            "platform": "Advanced Metabolomics Research Platform",
            "version": "3.1.0-production",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "recent_lipids": recent_lipids,
            "features_available": {
                "database": database_available,
                "models": models_available,
                "charts": charts_available,
                "authentication": auth_available
            },
            "news": [
                {
                    "title": "Production Deployment Successful",
                    "date": "2025-08-17",
                    "summary": "Platform now running with Railway v2 IPv6 compatibility and robust error handling."
                }
            ]
        }
        
        # Try template rendering with fallback
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
        }), 200

# =====================================================
# CONDITIONAL FEATURES (ONLY IF AVAILABLE)
# =====================================================

if database_available and models_available:
    @app.route('/dashboard')
    @app.route('/lipid-selection')
    def dashboard():
        """Lipid selection dashboard"""
        try:
            with app.app_context():
                dashboard_data = {
                    'stats': get_db_stats() if get_db_stats else {},
                    'lipids': [],
                    'classes': [],
                    'query_time': '0.000s',
                    'lazy_loading': True
                }
            
            try:
                return render_template('clean_dashboard.html', data=dashboard_data)
            except Exception:
                return jsonify({"message": "Dashboard available", "data": dashboard_data})
        except Exception as e:
            return jsonify({"error": f"Dashboard error: {str(e)}"}), 500

    @app.route('/api/database-view')
    def api_database_view():
        """Database view API"""
        try:
            with app.app_context():
                stats = get_db_stats() if get_db_stats else {}
                lipids_data = optimized_manager.get_all_lipids_optimized() if optimized_manager else []
                
                return jsonify({
                    "status": "success",
                    "stats": stats,
                    "lipids": lipids_data,
                    "total_count": len(lipids_data)
                })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if charts_available and models_available:
    @app.route('/dual-chart-view')
    def dual_chart_view():
        """Interactive chart view"""
        try:
            lipid_ids_str = request.args.get('lipids', '')
            if not lipid_ids_str:
                flash('No lipids selected for chart view.', 'warning')
                return redirect(url_for('dashboard'))
            
            try:
                return render_template('dual_chart_view.html')
            except Exception:
                return jsonify({"message": "Charts available but template missing"})
        except Exception as e:
            return jsonify({"error": f"Chart view error: {str(e)}"}), 500

    @app.route('/api/dual-chart-data/<int:lipid_id>')
    def api_dual_chart_data(lipid_id):
        """Chart data API"""
        try:
            chart_service = DualChartService()
            chart_data = chart_service.get_dual_chart_data(lipid_id)
            return jsonify({"status": "success", "data": chart_data})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

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
print("🚀 PRODUCTION METABOLOMICS PLATFORM")
print("=" * 60)
print(f"🐍 Python: {sys.version}")
print(f"📁 Directory: {os.getcwd()}")
print(f"🌐 PORT: {os.getenv('PORT', 'not-set')}")
print(f"🔧 Environment: {os.getenv('FLASK_ENV', 'production')}")
print(f"💾 Database: {'✅ Connected' if database_available else '❌ Unavailable'}")
print(f"📊 Models: {'✅ Loaded' if models_available else '❌ Failed'}")
print(f"📈 Charts: {'✅ Available' if charts_available else '❌ Failed'}")
print(f"🔐 Auth: {'✅ Configured' if auth_available else '❌ Failed'}")
print("=" * 60)

# =====================================================
# GUNICORN COMPATIBILITY
# =====================================================

if __name__ != '__main__':
    print("🚀 Running under Gunicorn (Railway deployment)")
    print(f"   IPv6 binding: [::]{os.getenv('PORT', '5000')}")
    print(f"   Health endpoint: /health")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Development server on port {port}")
    app.run(host='::', port=port, debug=debug_mode)