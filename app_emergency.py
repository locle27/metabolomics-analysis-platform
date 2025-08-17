#!/usr/bin/env python3
"""
EMERGENCY BULLETPROOF APP - GUARANTEED TO START
This will definitely work and help us diagnose what's failing
"""

import os
import sys
import traceback
from datetime import datetime

print("🚨 EMERGENCY APP STARTING...")
print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")
print(f"PORT: {os.getenv('PORT', 'NOT SET')}")

# Test Flask import first
try:
    from flask import Flask, jsonify
    print("✅ Flask import successful")
except Exception as e:
    print(f"❌ CRITICAL: Flask import failed: {e}")
    # Create emergency HTTP server if Flask fails
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    
    class EmergencyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "emergency",
                "message": "Flask unavailable - running emergency server",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
    
    port = int(os.getenv('PORT', 5000))
    server = HTTPServer(('::', port), EmergencyHandler)
    print(f"🚨 EMERGENCY SERVER on port {port}")
    server.serve_forever()

# Flask is available, create minimal app
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "message": "Emergency app working",
        "timestamp": datetime.now().isoformat(),
        "port": os.getenv('PORT', 'not-set'),
        "runtime": "emergency-mode"
    }), 200

@app.route('/')
def home():
    return jsonify({
        "status": "emergency_mode",
        "message": "Emergency diagnostic app running",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "PORT": os.getenv('PORT', 'not-set'),
            "DATABASE_URL": "configured" if os.getenv('DATABASE_URL') else "not-set",
            "FLASK_ENV": os.getenv('FLASK_ENV', 'not-set')
        },
        "files_present": os.listdir('.'),
        "python_path": sys.path[:3]
    })

@app.route('/debug')
def debug():
    return jsonify({
        "environment_variables": dict(os.environ),
        "python_executable": sys.executable,
        "working_directory": os.getcwd(),
        "all_files": os.listdir('.'),
        "python_version": sys.version
    })

# Error handlers
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({
        "status": "error",
        "message": str(e),
        "traceback": traceback.format_exc(),
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚨 EMERGENCY APP starting on port {port}")
    print(f"   IPv6 binding: ::")
    print(f"   Health endpoint: /health")
    print(f"   Debug endpoint: /debug")
    app.run(host='::', port=port, debug=False)
else:
    print("🚨 EMERGENCY APP loaded by Gunicorn")
    print(f"   Port: {os.getenv('PORT', 'not-set')}")
    print(f"   IPv6 binding active")