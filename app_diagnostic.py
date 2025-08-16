#!/usr/bin/env python3
"""
Diagnostic version to identify Railway startup issues
"""

import sys
import traceback
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def diagnostic():
    return """
    <h1>🔍 Diagnostic Mode</h1>
    <p>✅ Flask is working</p>
    <p>✅ Python imports successful</p>
    <p>Ready to test step by step...</p>
    """

@app.route('/test-imports')
def test_imports():
    results = []
    
    # Test 1: Basic imports
    try:
        import os
        import logging
        from flask import render_template, request, redirect, url_for, flash, jsonify
        results.append("✅ Basic Flask imports working")
    except Exception as e:
        results.append(f"❌ Basic imports failed: {e}")
    
    # Test 2: Database imports
    try:
        from sqlalchemy import text
        from sqlalchemy.orm import joinedload, selectinload
        results.append("✅ SQLAlchemy imports working")
    except Exception as e:
        results.append(f"❌ SQLAlchemy imports failed: {e}")
    
    # Test 3: Authentication imports
    try:
        from flask_login import LoginManager, login_user, logout_user, login_required, current_user
        from authlib.integrations.flask_client import OAuth
        results.append("✅ Authentication imports working")
    except Exception as e:
        results.append(f"❌ Authentication imports failed: {e}")
    
    # Test 4: Email imports
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        results.append("✅ Email imports working")
    except Exception as e:
        results.append(f"❌ Email imports failed: {e}")
    
    # Test 5: Custom model imports
    try:
        from models_postgresql_optimized import db, User, MainLipid
        results.append("✅ Custom model imports working")
    except Exception as e:
        results.append(f"❌ Custom model imports failed: {e}")
        results.append(f"📋 Traceback: {traceback.format_exc()}")
    
    # Test 6: Email service imports
    try:
        from email_service_simple import send_email, test_email_configuration
        results.append("✅ Email service imports working")
    except Exception as e:
        results.append(f"❌ Email service imports failed: {e}")
        results.append(f"📋 Traceback: {traceback.format_exc()}")
    
    # Test 7: Auth blueprint imports
    try:
        from email_auth_production import auth_bp
        results.append("✅ Auth blueprint imports working")
    except Exception as e:
        results.append(f"❌ Auth blueprint imports failed: {e}")
        results.append(f"📋 Traceback: {traceback.format_exc()}")
    
    html = "<h1>🔍 Import Diagnostic Results</h1><ul>"
    for result in results:
        html += f"<li>{result}</li>"
    html += "</ul>"
    
    return html

@app.route('/test-env')
def test_env():
    """Test environment variables"""
    env_vars = [
        'DATABASE_URL',
        'SECRET_KEY', 
        'FLASK_ENV',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'GOOGLE_CLIENT_ID'
    ]
    
    html = "<h1>🔍 Environment Variables</h1><ul>"
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'PASSWORD' in var or 'SECRET' in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            html += f"<li>✅ {var}: {display_value}</li>"
        else:
            html += f"<li>❌ {var}: NOT SET</li>"
    html += "</ul>"
    
    return html

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)