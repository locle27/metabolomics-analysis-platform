#!/usr/bin/env python3
"""
Minimal Flask App for Railway Debugging
This version should start successfully to test Railway deployment
"""

import os
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

# Create Flask app
app = Flask(__name__)

# Fix for Railway HTTPS proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)

# Basic configuration
app.secret_key = os.getenv('SECRET_KEY', 'railway-test-key')

@app.route('/')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'message': 'Metabolomics Platform is running!',
        'environment': os.getenv('FLASK_ENV', 'development'),
        'port': os.getenv('PORT', '5000'),
        'domain': os.getenv('CUSTOM_DOMAIN', 'Not set')
    })

@app.route('/test')
def test_endpoint():
    """Simple test endpoint"""
    return jsonify({
        'message': 'Railway deployment successful!',
        'environment_vars': {
            'DATABASE_URL': 'Set' if os.getenv('DATABASE_URL') else 'Missing',
            'GOOGLE_CLIENT_ID': 'Set' if os.getenv('GOOGLE_CLIENT_ID') else 'Missing',
            'MAIL_USERNAME': 'Set' if os.getenv('MAIL_USERNAME') else 'Missing'
        }
    })

@app.route('/env-check')
def env_check():
    """Check environment variables"""
    required_vars = [
        'DATABASE_URL', 'SECRET_KEY', 'FLASK_ENV',
        'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET',
        'MAIL_USERNAME', 'MAIL_PASSWORD', 'CUSTOM_DOMAIN'
    ]
    
    env_status = {}
    for var in required_vars:
        env_status[var] = 'Set' if os.getenv(var) else 'Missing'
    
    return jsonify({
        'status': 'Environment Check',
        'variables': env_status,
        'missing_count': sum(1 for v in env_status.values() if v == 'Missing')
    })

if __name__ == '__main__':
    # Railway configuration
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    print(f"🚀 Starting Minimal Flask App for Railway")
    print(f"   Port: {port}")
    print(f"   Debug: {debug_mode}")
    print(f"   Environment: {os.getenv('FLASK_ENV', 'development')}")
    
    # Run the app
    app.run(debug=debug_mode, host='0.0.0.0', port=port)