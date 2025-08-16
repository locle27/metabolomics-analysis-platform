#!/usr/bin/env python3
"""
Absolute minimal Flask app for Railway healthcheck debugging
"""

import os
import sys
from datetime import datetime

print(f"🐍 Python version: {sys.version}")
print(f"🐍 Python executable: {sys.executable}")
print(f"📁 Current working directory: {os.getcwd()}")
print(f"🔧 Environment variables:")
for key in ['DATABASE_URL', 'SECRET_KEY', 'FLASK_ENV', 'PORT']:
    value = os.getenv(key, 'NOT SET')
    if key == 'DATABASE_URL' and value != 'NOT SET':
        # Mask sensitive database URL
        value = value[:30] + "...MASKED..."
    print(f"   {key}: {value}")

# Test Flask import
try:
    from flask import Flask
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")
    sys.exit(1)

# Create minimal app
app = Flask(__name__)

@app.route('/')
def health():
    return {
        "status": "healthy",
        "message": "Minimal Flask app running successfully",
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "environment": os.getenv('FLASK_ENV', 'unknown')
    }

@app.route('/health')
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Starting minimal Flask app on port {port}")
    print(f"   Flask version: {Flask.__version__ if hasattr(Flask, '__version__') else 'unknown'}")
    
    try:
        app.run(debug=False, host='0.0.0.0', port=port)
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        sys.exit(1)
