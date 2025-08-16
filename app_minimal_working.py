#!/usr/bin/env python3
"""
Minimal working version to get Railway back online
Then we can add email features step by step
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from werkzeug.middleware.proxy_fix import ProxyFix
import json
from pathlib import Path

# Simple configuration
BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=BASE_DIR / "templates", static_folder=BASE_DIR / "static")

# Fix for Railway HTTPS proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
app.secret_key = os.getenv('SECRET_KEY', 'metabolomics-dev-key-change-in-production')

@app.route('/')
def homepage():
    """Simple homepage that works"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Metabolomics Platform</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #2E4C92; }
            .status { background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .button { background: #2E4C92; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; display: inline-block; }
        </style>
    </head>
    <body>
        <h1>🧬 Metabolomics Platform</h1>
        <div class="status">
            <h3>✅ System Status: Online</h3>
            <p>The platform is running successfully on Railway!</p>
        </div>
        
        <h2>🚀 Available Features:</h2>
        <div>
            <a href="/test-database" class="button">🗄️ Test Database</a>
            <a href="/test-email-import" class="button">📧 Test Email Import</a>
            <a href="/demo-login" class="button">👤 Demo Login</a>
            <a href="/schedule" class="button">📅 Schedule Test</a>
        </div>
        
        <h2>📊 Next Steps:</h2>
        <ol>
            <li>✅ Basic Flask app working</li>
            <li>🔄 Test database connection</li>
            <li>🔄 Add email functionality</li>
            <li>🔄 Add authentication</li>
            <li>🔄 Add full features</li>
        </ol>
    </body>
    </html>
    """

@app.route('/test-database')
def test_database():
    """Test database connection"""
    try:
        # Try to import database modules
        from models_postgresql_optimized import db, MainLipid
        return jsonify({
            'status': 'success',
            'message': 'Database models imported successfully',
            'database_url': os.getenv('DATABASE_URL', 'Not set')[:50] + '...'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database import failed: {str(e)}',
            'database_url': os.getenv('DATABASE_URL', 'Not set')[:50] + '...'
        })

@app.route('/test-email-import')
def test_email_import():
    """Test email service import"""
    try:
        from email_service_simple import send_email, test_email_configuration
        return jsonify({
            'status': 'success',
            'message': 'Email service imported successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Email service import failed: {str(e)}'
        })

@app.route('/demo-login')
def demo_login():
    """Simple demo login without database"""
    return """
    <h1>🎯 Demo Login</h1>
    <p>✅ Demo login would work here</p>
    <p>⚠️ Need to add database and authentication</p>
    <a href="/">← Back to Home</a>
    """

@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    """Simple scheduling form"""
    if request.method == 'POST':
        return """
        <h1>📅 Schedule Request Submitted</h1>
        <p>✅ Form submission works</p>
        <p>⚠️ Need to add email functionality</p>
        <a href="/">← Back to Home</a>
        """
    
    return """
    <h1>📅 Schedule Consultation</h1>
    <form method="POST">
        <p><input type="text" name="name" placeholder="Your Name" required></p>
        <p><input type="email" name="email" placeholder="Your Email" required></p>
        <p><textarea name="message" placeholder="Message"></textarea></p>
        <p><button type="submit">Submit Request</button></p>
    </form>
    <a href="/">← Back to Home</a>
    """

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'metabolomics-platform',
        'environment': os.getenv('FLASK_ENV', 'development')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)