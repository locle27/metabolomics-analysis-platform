#!/usr/bin/env python3
"""
Minimal Flask app to test Railway deployment
This will help isolate what's causing the healthcheck failures
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def health_check():
    """Simple health check route"""
    return {
        "status": "healthy",
        "message": "Minimal Flask app is running!",
        "environment": os.getenv('FLASK_ENV', 'development'),
        "port": os.getenv('PORT', '5000')
    }

@app.route('/test')
def test_route():
    """Test route to verify app is working"""
    return {"test": "success", "timestamp": "2025-08-17"}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🧪 Starting MINIMAL test app on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)