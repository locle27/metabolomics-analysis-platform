#!/usr/bin/env python3
"""
ULTRA-MINIMAL FLASK APP FOR RAILWAY DEPLOYMENT
Guaranteed to work with basic dependencies and pass health checks
"""

import os
import sys
import json
from datetime import datetime

print("🚀 MINIMAL METABOLOMICS PLATFORM STARTING")
print(f"🐍 Python: {sys.version}")
print(f"📁 Directory: {os.getcwd()}")
print(f"📡 Port: {os.getenv('PORT', '5000')}")

# Basic Flask app - guaranteed to work
try:
    from flask import Flask, jsonify, render_template_string
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ CRITICAL: Flask import failed: {e}")
    sys.exit(1)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-minimal')

# Basic database connection (optional)
database_available = False
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment loaded")
    
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        from flask_sqlalchemy import SQLAlchemy
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy()
        db.init_app(app)
        
        # Test database
        with app.app_context():
            from sqlalchemy import text
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                database_available = True
                print("✅ Database connected")
    else:
        print("⚠️ No DATABASE_URL - running without database")
        
except Exception as e:
    print(f"⚠️ Database setup failed: {e}")

# === ROUTES ===

@app.route('/health')
def health_check():
    """Railway health check - MUST return 200"""
    return jsonify({
        "status": "healthy",
        "message": "Minimal metabolomics platform operational",
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version.split()[0],
        "port": os.getenv('PORT', '5000'),
        "database": "connected" if database_available else "unavailable"
    }), 200

@app.route('/')
def homepage():
    """Simple homepage"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Metabolomics Platform - Minimal Version</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; }
            .warning { background: #fff3cd; border: 1px solid #ffeaa7; }
        </style>
    </head>
    <body>
        <h1>🧬 Metabolomics Research Platform</h1>
        <h2>Minimal Deployment Version</h2>
        
        <div class="status success">
            <strong>✅ Status:</strong> Platform operational
        </div>
        
        <div class="status {{ 'success' if database_available else 'warning' }}">
            <strong>🗄️ Database:</strong> {{ 'Connected' if database_available else 'Unavailable' }}
        </div>
        
        <h3>System Information</h3>
        <ul>
            <li><strong>Python Version:</strong> {{ python_version }}</li>
            <li><strong>Environment:</strong> {{ environment }}</li>
            <li><strong>Timestamp:</strong> {{ timestamp }}</li>
        </ul>
        
        <h3>Available Endpoints</h3>
        <ul>
            <li><a href="/health">/health</a> - Health check for Railway</li>
            <li><a href="/debug">/debug</a> - System debug information</li>
        </ul>
        
        <p><em>This is a minimal version designed to ensure reliable deployment. 
        Full features will be added once basic deployment is stable.</em></p>
    </body>
    </html>
    """
    
    return render_template_string(html, 
        database_available=database_available,
        python_version=sys.version.split()[0],
        environment=os.getenv('FLASK_ENV', 'production'),
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    )

@app.route('/debug')
def debug_info():
    """Debug information for troubleshooting"""
    debug_data = {
        "system": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "environment_variables": {
                "PORT": os.getenv('PORT'),
                "FLASK_ENV": os.getenv('FLASK_ENV'),
                "DATABASE_URL": "configured" if os.getenv('DATABASE_URL') else "not_set"
            }
        },
        "flask": {
            "version": "imported_successfully",
            "secret_key": "configured" if app.secret_key else "not_set"
        },
        "database": {
            "available": database_available,
            "url_configured": bool(os.getenv('DATABASE_URL'))
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(debug_data)

# === APPLICATION STARTUP ===

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🌐 Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    print("✅ Flask app initialized for gunicorn")

# For gunicorn
application = app

print("🎯 MINIMAL PLATFORM READY")