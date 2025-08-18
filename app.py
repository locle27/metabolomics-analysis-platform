#!/usr/bin/env python3
"""
BULLETPROOF METABOLOMICS PLATFORM - Original Interface Preserved
All original features, navigation, templates, and styling preserved
Enhanced with bulletproof deployment patterns for Railway compatibility
"""

import os
import sys
import json
import base64
import time
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from io import BytesIO
# Try to load dotenv, but don't fail if not available (Railway sets env vars directly)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("ℹ️ python-dotenv not available, using system environment variables")

print("🚀 BULLETPROOF METABOLOMICS PLATFORM STARTING")
print(f"📡 Port: {os.getenv('PORT', '5000')}")
print("=" * 60)

# === BULLETPROOF IMPORTS ===
# Core Flask (REQUIRED)
try:
    from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, send_file, session, get_flashed_messages, make_response, current_app
    print("✅ Flask core loaded")
except ImportError as e:
    print(f"❌ CRITICAL: Flask failed: {e}")
    sys.exit(1)

# Environment loading (graceful fallback)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment loaded")
except:
    print("⚠️ Environment loading failed - using defaults")

# Proxy fix (graceful fallback)
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    PROXY_FIX_AVAILABLE = True
    print("✅ Proxy fix available")
except:
    PROXY_FIX_AVAILABLE = False
    print("⚠️ Proxy fix unavailable")

# SQLAlchemy (graceful fallback)
try:
    from sqlalchemy import text
    from sqlalchemy.orm import joinedload, selectinload
    SQLALCHEMY_AVAILABLE = True
    print("✅ SQLAlchemy available")
except:
    SQLALCHEMY_AVAILABLE = False
    print("⚠️ SQLAlchemy unavailable")

# Authentication imports (graceful fallback)
try:
    from flask_login import LoginManager, login_user, logout_user, login_required, current_user
    LOGIN_MANAGER_AVAILABLE = True
    print("✅ Flask-Login available")
except:
    LOGIN_MANAGER_AVAILABLE = False
    print("⚠️ Flask-Login unavailable")

try:
    from authlib.integrations.flask_client import OAuth
    OAUTH_AVAILABLE = True
    print("✅ OAuth available")
except:
    OAUTH_AVAILABLE = False
    print("⚠️ OAuth unavailable")

try:
    from flask_mail import Mail, Message
    MAIL_AVAILABLE = True
    print("✅ Flask-Mail available")
except:
    MAIL_AVAILABLE = False
    print("⚠️ Flask-Mail unavailable")

try:
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect()
    CSRF_AVAILABLE = True
    print("✅ CSRF protection available")
except:
    CSRF_AVAILABLE = False
    print("⚠️ CSRF protection unavailable")

# === FLASK APP CONFIGURATION ===
BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, 
    template_folder=BASE_DIR / "templates", 
    static_folder=BASE_DIR / "static"
)

# URGENT: Add immediate health checks for deployment
@app.route('/health')
def immediate_health_check():
    """Immediate health check available before full app initialization"""
    return "OK", 200

@app.route('/ping')
def immediate_ping():
    """Immediate ping endpoint"""
    return "pong", 200

@app.route('/healthz')
def immediate_healthz():
    """Immediate Kubernetes-style health check"""
    return "OK", 200

# Enhanced SECRET_KEY configuration with debug info
SECRET_KEY = os.getenv('SECRET_KEY', 'bulletproof-metabolomics-platform-secret-key-for-local-dev')
app.secret_key = SECRET_KEY
print(f"✅ SECRET_KEY configured: {len(SECRET_KEY)} characters, from env: {bool(os.getenv('SECRET_KEY'))}")

# Enhanced session configuration for OAuth
app.config.update({
    'SESSION_COOKIE_SECURE': False,  # Allow both HTTP and HTTPS
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    # Remove custom cookie name - use Flask default 'session'
    'SESSION_COOKIE_PATH': '/',  # Available for all paths
    'PERMANENT_SESSION_LIFETIME': timedelta(hours=1),  # 1 hour
    'SESSION_REFRESH_EACH_REQUEST': True,  # Keep session alive
    # WTF-CSRF Configuration (Following Flask-WTF docs)
    'WTF_CSRF_ENABLED': True,
    'WTF_CSRF_TIME_LIMIT': None,  # Token valid for session lifetime
    'WTF_CSRF_SSL_STRICT': False,  # Allow HTTP for development
    'WTF_CSRF_CHECK_DEFAULT': True,
    'WTF_CSRF_SECRET_KEY': SECRET_KEY,  # Explicitly set CSRF secret key
})

# Enable CSRF protection properly with error handling
if CSRF_AVAILABLE:
    try:
        csrf.init_app(app)
        print("✅ CSRF protection initialized successfully")
        print(f"🔍 CSRF SECRET_KEY available: {bool(app.config.get('WTF_CSRF_SECRET_KEY'))}")
        print(f"🔍 App SECRET_KEY available: {bool(app.secret_key)}")
        
        # Add CSRF error handler following Flask documentation
        from flask_wtf.csrf import CSRFError
        @app.errorhandler(CSRFError)
        def handle_csrf_error(e):
            # Simple CSRF error handler that won't interfere with health checks
            print(f"❌ CSRF Error: {e.description}")
            return 'CSRF Error: Security token expired. Please refresh the page and try again.', 400
            
    except Exception as csrf_init_error:
        print(f"❌ CSRF initialization failed: {csrf_init_error}")
        print(f"🔍 SECRET_KEY length: {len(app.secret_key) if app.secret_key else 0}")
        CSRF_AVAILABLE = False
    
    # Exempt routes from CSRF protection
    OAUTH_EXEMPT_ROUTES = [
        'login_authorized', 'auth.oauth_authorized', 'oauth_login',
        'immediate_health_check', 'immediate_ping', 'immediate_healthz'  # Health checks
    ]
    
    # TEMPORARY: Add password update for debugging
    CSRF_DEBUG_EXEMPT_ROUTES = [
        'auth.update_password'
    ]
    
    OAUTH_EXEMPT_PATHS = ['/callback', '/authorized', '/health', '/ping', '/healthz']
    
    # TEMPORARY: Add password update path for debugging
    CSRF_DEBUG_EXEMPT_PATHS = ['/auth/update-password']
    
    @app.before_request
    def disable_csrf_for_oauth_routes():
        """Disable CSRF only for OAuth callback routes"""
        try:
            # Check OAuth endpoints
            if request.endpoint in OAUTH_EXEMPT_ROUTES:
                print(f"🔓 CSRF disabled for OAuth endpoint: {request.endpoint}")
                return None
            
            # TEMPORARY: Check debug exempt endpoints 
            if request.endpoint in CSRF_DEBUG_EXEMPT_ROUTES:
                print(f"🔓 CSRF TEMPORARILY disabled for debugging endpoint: {request.endpoint}")
                return None
            
            # Check OAuth paths
            for path in OAUTH_EXEMPT_PATHS:
                if path in request.path:
                    print(f"🔓 CSRF disabled for OAuth path: {request.path}")
                    return None
            
            # TEMPORARY: Check debug exempt paths
            for path in CSRF_DEBUG_EXEMPT_PATHS:
                if path in request.path:
                    print(f"🔓 CSRF TEMPORARILY disabled for debugging path: {request.path}")
                    return None
                    
        except Exception as e:
            print(f"⚠️ OAuth CSRF exemption error: {e}")
    
    print("✅ CSRF protection enabled with proper token handling")
else:
    print("⚠️ CSRF protection not available")

# Global CSRF token context processor (works even if CSRF is disabled)
@app.context_processor
def global_csrf_token():
    """Provide CSRF token to all templates with fallback"""
    try:
        if CSRF_AVAILABLE:
            from flask_wtf.csrf import generate_csrf
            return dict(csrf_token=generate_csrf)
        else:
            return dict(csrf_token=lambda: "")
    except Exception as e:
        print(f"⚠️ Global CSRF token error: {e}")
        return dict(csrf_token=lambda: "")

# Test route for CSRF token
@app.route('/test-csrf')
def test_csrf():
    """Test CSRF token generation"""
    try:
        if CSRF_AVAILABLE:
            from flask_wtf.csrf import generate_csrf
            token = generate_csrf()
            return f"CSRF token generated: {token[:10]}..."
        else:
            return "CSRF not available"
    except Exception as e:
        return f"CSRF test error: {e}"

@app.route('/debug-csrf')
def debug_csrf():
    """Comprehensive CSRF debugging"""
    debug_info = {
        "CSRF_AVAILABLE": CSRF_AVAILABLE,
        "SECRET_KEY_SET": bool(app.secret_key),
        "SECRET_KEY_LENGTH": len(app.secret_key) if app.secret_key else 0,
        "SESSION_COOKIE_SECURE": app.config.get('SESSION_COOKIE_SECURE'),
        "SESSION_COOKIE_HTTPONLY": app.config.get('SESSION_COOKIE_HTTPONLY'),
        "SESSION_COOKIE_SAMESITE": app.config.get('SESSION_COOKIE_SAMESITE'),
    }
    
    try:
        if CSRF_AVAILABLE:
            from flask_wtf.csrf import generate_csrf
            token = generate_csrf()
            debug_info["CSRF_TOKEN_GENERATED"] = True
            debug_info["CSRF_TOKEN_LENGTH"] = len(token)
            debug_info["CSRF_TOKEN_PREVIEW"] = token[:10] + "..."
        else:
            debug_info["CSRF_TOKEN_GENERATED"] = False
    except Exception as e:
        debug_info["CSRF_TOKEN_ERROR"] = str(e)
    
    # Test forms import
    try:
        from forms import PasswordUpdateForm
        debug_info["FORMS_IMPORT"] = "SUCCESS"
        form = PasswordUpdateForm()
        debug_info["FORMS_INSTANTIATION"] = "SUCCESS"
    except Exception as e:
        debug_info["FORMS_IMPORT_ERROR"] = str(e)
    
    return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"

@app.route('/test-wtform', methods=['GET', 'POST'])
def test_wtform():
    """Test WTForm with CSRF"""
    try:
        from forms import PasswordUpdateForm
    except ImportError as e:
        return f"Forms import error: {e}"
    
    form = PasswordUpdateForm()
    
    if request.method == 'POST':
        print(f"🔍 POST request received")
        print(f"🔍 Form data: {dict(request.form)}")
        print(f"🔍 Form errors before validation: {form.errors}")
        
        if form.validate_on_submit():
            return "✅ Form validation successful!"
        else:
            print(f"❌ Form validation failed: {form.errors}")
            return f"❌ Form validation failed: {form.errors}"
    
    # GET request - show form
    return f"""
    <h2>Test WTForm with CSRF</h2>
    <form method="POST">
        {form.hidden_tag()}
        <p>
            {form.new_password.label}<br>
            {form.new_password}
        </p>
        <p>
            {form.confirm_password.label}<br>
            {form.confirm_password}
        </p>
        <p>
            {form.submit()}
        </p>
    </form>
    """

@app.route('/test-basic-csrf', methods=['GET', 'POST'])
def test_basic_csrf():
    """Test basic CSRF without WTForms"""
    if request.method == 'POST':
        print(f"🔍 Basic CSRF test - POST received")
        print(f"🔍 Form data: {dict(request.form)}")
        
        # Try manual CSRF validation
        if CSRF_AVAILABLE:
            try:
                from flask_wtf.csrf import validate_csrf
                csrf_token = request.form.get('csrf_token', '')
                validate_csrf(csrf_token)
                return "✅ Basic CSRF validation successful!"
            except Exception as e:
                return f"❌ Basic CSRF validation failed: {e}"
        else:
            return "❌ CSRF not available"
    
    # GET - generate form with manual CSRF token
    csrf_token = ""
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()
        except Exception as e:
            return f"CSRF generation error: {e}"
    
    return f"""
    <h2>Basic CSRF Test (No WTForms)</h2>
    <form method="POST">
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        <p>
            <label>Test Input:</label><br>
            <input type="text" name="test_field" required>
        </p>
        <p>
            <input type="submit" value="Submit Test">
        </p>
    </form>
    <p>CSRF Token: <code>{csrf_token[:20]}...</code></p>
    """

@app.route('/ultra-simple-csrf', methods=['GET', 'POST'])
def ultra_simple_csrf():
    """Ultra simple CSRF test with minimal code"""
    print(f"\n🔍 ULTRA SIMPLE CSRF TEST - {request.method}")
    
    if request.method == 'POST':
        print(f"🔍 POST received - Form data: {dict(request.form)}")
        
        # Just return success without any redirects or complex logic
        return """
        <h1 style="color: green;">✅ ULTRA SIMPLE TEST SUCCESS!</h1>
        <p>POST request processed successfully without CSRF error!</p>
        <p><a href="/ultra-simple-csrf">Try Again</a></p>
        """
    
    # GET request - show ultra simple form
    csrf_token = ""
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()
            print(f"🔍 CSRF token generated: {csrf_token[:20]}...")
        except Exception as e:
            print(f"❌ CSRF generation failed: {e}")
            return f"CSRF Error: {e}"
    
    return f"""
    <h2>🔍 Ultra Simple CSRF Test</h2>
    <p>This is the simplest possible test with no redirects or complex logic.</p>
    
    <form method="POST">
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        <p>
            <label>Simple test:</label><br>
            <input type="text" name="test" value="hello" required>
        </p>
        <p>
            <input type="submit" value="Test CSRF">
        </p>
    </form>
    
    <h3>Debug Info:</h3>
    <pre>
CSRF Available: {CSRF_AVAILABLE}
Token Length: {len(csrf_token)}
Token Preview: {csrf_token[:30]}...
Session Keys: {list(session.keys())}
Request Method: {request.method}
    </pre>
    """

@app.route('/session-test')
def session_test():
    """Test session persistence - simplified"""
    old_counter = session.get('test_counter', 0)
    session['test_counter'] = old_counter + 1
    session['test_time'] = datetime.now().isoformat()
    session.permanent = True
    
    # Debug session details
    secret_key_hash = hash(app.secret_key) if app.secret_key else None
    
    # Check which cookie is being used by Flask
    active_cookie = request.cookies.get('session', 'NOT_FOUND')
    metabolomics_cookie = request.cookies.get('metabolomics_session', 'NOT_FOUND')
    
    return f"""
    <h2>🔬 Session Debug</h2>
    <pre>
<strong>Session Data:</strong>
Old Counter: {old_counter}
New Counter: {session.get('test_counter', 0)}
Time: {session.get('test_time', 'Not set')}
All Keys: {list(session.keys())}
Permanent: {session.permanent}

<strong>Cookie Analysis:</strong>
Flask 'session' cookie: {active_cookie[:50] if active_cookie != 'NOT_FOUND' else 'NOT_FOUND'}...
'metabolomics_session' cookie: {metabolomics_cookie[:50] if metabolomics_cookie != 'NOT_FOUND' else 'NOT_FOUND'}...

<strong>Configuration:</strong>
SECRET_KEY length: {len(app.secret_key) if app.secret_key else 0}
SECRET_KEY hash: {secret_key_hash}
SECRET_KEY from env: {bool(os.getenv('SECRET_KEY'))}
Cookie name: {app.config.get('SESSION_COOKIE_NAME', 'session')}

<strong>Request:</strong>
Cookies: {list(request.cookies.keys())}
Host: {request.host}
    </pre>
    <p><a href="/session-test" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none;">🔄 Refresh Test</a></p>
    <p><a href="/clear-cookies" style="padding: 10px 20px; background: #dc3545; color: white; text-decoration: none;">🗑️ Clear Cookies</a></p>
    <p><a href="/auth/login" style="padding: 10px 20px; background: #28a745; color: white; text-decoration: none;">🔐 Test Login</a></p>
    <hr>
    <p><strong>🔍 Diagnosis:</strong></p>
    <p><em>Old Counter: {old_counter}, New Counter: {session.get('test_counter', 0)}</em></p>
    <p><em>If Old = New = 0, Flask is reading wrong cookie or secret key issue.</em></p>
    <p><em>If Old != New, sessions work but not persisting between requests.</em></p>
    """

@app.route('/clear-cookies')
def clear_cookies():
    """Clear conflicting session cookies"""
    response = make_response(redirect(url_for('session_test')))
    
    # Clear both potential session cookies
    response.set_cookie('session', '', expires=0, path='/')
    response.set_cookie('metabolomics_session', '', expires=0, path='/')
    
    # Clear session data
    session.clear()
    
    flash('All cookies cleared. Test session persistence again.', 'info')
    return response

@app.route('/password-help')
def password_help():
    """Show password requirements and examples"""
    return """
    <h2>🔐 Password Requirements & Examples</h2>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3>Requirements:</h3>
        <ul>
            <li>✅ At least 8 characters long</li>
            <li>✅ At least one UPPERCASE letter (A-Z)</li>
            <li>✅ At least one lowercase letter (a-z)</li>
            <li>✅ At least one number (0-9)</li>
            <li>✅ At least one special character (!@#$%^&*)</li>
        </ul>
    </div>
    
    <div style="background: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3>✅ Valid Password Examples:</h3>
        <ul>
            <li><code>Password123!</code> - Simple and effective</li>
            <li><code>MySecure2024#</code> - Easy to remember</li>
            <li><code>Test@2024</code> - Short but valid</li>
            <li><code>Admin123$</code> - Works for testing</li>
        </ul>
    </div>
    
    <div style="background: #f8d7da; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3>❌ Invalid Examples (and why):</h3>
        <ul>
            <li><code>password123</code> - Missing uppercase & special char</li>
            <li><code>PASSWORD123</code> - Missing lowercase & special char</li>
            <li><code>Password</code> - Missing number & special char</li>
            <li><code>Pass1!</code> - Too short (less than 8 chars)</li>
        </ul>
    </div>
    
    <p><a href="/auth/update-password">→ Try Password Update</a></p>
    <p><a href="/test-wtform">→ Test Simple Form</a></p>
    """

@app.route('/password-success')
def password_success():
    """Simple password update success page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Password Updated - Metabolomics Platform</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center mt-5">
                <div class="col-md-6">
                    <div class="card border-0 shadow">
                        <div class="card-body text-center p-5">
                            <div class="mb-4">
                                <i class="fas fa-check-circle text-success" style="font-size: 4rem;"></i>
                            </div>
                            <h2 class="text-success mb-3">Password Updated Successfully!</h2>
                            <p class="text-muted mb-4">Your password has been updated securely. You can now use your new password to log in.</p>
                            
                            <div class="d-grid gap-2">
                                <a href="/auth/profile" class="btn btn-primary">
                                    <i class="fas fa-user"></i> Go to Profile
                                </a>
                                <a href="/" class="btn btn-outline-secondary">
                                    <i class="fas fa-home"></i> Go to Dashboard
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/simple-password-test', methods=['GET', 'POST'])
def simple_password_test():
    """Simple password test without WTForms complexity"""
    print(f"\n🔍 SIMPLE PASSWORD TEST - {request.method}")
    
    if request.method == 'POST':
        print(f"🔍 POST received")
        print(f"🔍 Form data: {dict(request.form)}")
        print(f"🔍 Session: {dict(session)}")
        
        # Simple success without redirects
        return """
        <h1 style="color: green;">✅ SIMPLE PASSWORD TEST SUCCESS!</h1>
        <p>Password form submitted successfully!</p>
        <p><a href="/simple-password-test">Try Again</a></p>
        <p><a href="/auth/update-password">Real Password Update</a></p>
        """
    
    # GET - simple form
    csrf_token = ""
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()
        except Exception as e:
            return f"CSRF Error: {e}"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Simple Password Test</title></head>
    <body style="font-family: Arial; margin: 40px;">
    
    <h2>🔐 Simple Password Test</h2>
    <p>Testing password form submission without complex WTForms</p>
    
    <form method="POST" style="background: #f5f5f5; padding: 20px; border-radius: 8px;">
        <input type="hidden" name="csrf_token" value="{csrf_token}">
        
        <p>
            <label>New Password:</label><br>
            <input type="password" name="new_password" value="Password123!" required style="padding: 8px; width: 200px;">
        </p>
        
        <p>
            <label>Confirm Password:</label><br>
            <input type="password" name="confirm_password" value="Password123!" required style="padding: 8px; width: 200px;">
        </p>
        
        <p>
            <input type="submit" value="Test Password Submit" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px;">
        </p>
    </form>
    
    <div style="background: #e9ecef; padding: 15px; border-radius: 5px; margin-top: 20px;">
        <h3>Debug Info:</h3>
        <pre>
CSRF Token: {csrf_token[:50]}...
Session Keys: {list(session.keys())}
User Email: {session.get('user_email', 'Not set')}
Authenticated: {session.get('user_authenticated', False)}
        </pre>
    </div>
    
    </body>
    </html>
    """

# Apply proxy fix if available
if PROXY_FIX_AVAILABLE:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
    print("✅ Railway proxy configured")

# Session persistence fix for production  
@app.before_request
def fix_session_persistence():
    """Fix session persistence issues in production"""
    # Skip all processing for health check routes
    if request.endpoint in ['ping', 'health', 'status', 'healthz']:
        return
    
    # Debug empty sessions - only for auth routes
    if request.endpoint and 'auth.' in str(request.endpoint) and len(session.keys()) == 0:
        print(f"🔍 DEBUG: Empty session on {request.endpoint}")
        print(f"🔍 Cookies: {list(request.cookies.keys())}")
        print(f"🔍 Flask session cookie name: {app.config.get('SESSION_COOKIE_NAME', 'session')}")
        print(f"🔍 SECRET_KEY consistent: {len(app.secret_key) == 39}")
        
        # Test session write
        session['test_debug'] = 'debug_value'
        print(f"🔍 After test write, session keys: {list(session.keys())}")
    
    # Only make sessions permanent for non-health routes
    if session:
        session.permanent = True

@app.after_request  
def after_request(response):
    """Minimal session processing"""
    # Skip all processing for health check routes
    if request.endpoint in ['ping', 'health', 'status', 'healthz']:
        return response
    
    return response

# === AUTHENTICATION SETUP (Working + Bulletproof) ===
login_manager = None
oauth = None
google = None

try:
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    print("✅ Login manager configured")
except Exception as e:
    print(f"⚠️ Login manager failed: {e}")

try:
    oauth = OAuth(app)
    google = oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'prompt': 'select_account'  # Force account selection to avoid state issues
        }
    )
    print("✅ OAuth configured with enhanced state handling")
except Exception as e:
    print(f"⚠️ OAuth failed: {e}")

# === EMAIL CONFIGURATION (Working + Bulletproof) ===
mail = None

try:
    app.config.update({
        'MAIL_SERVER': os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
        'MAIL_PORT': int(os.getenv('MAIL_PORT', 587)),
        'MAIL_USE_TLS': os.getenv('MAIL_USE_TLS', 'True').lower() == 'true',
        'MAIL_USERNAME': os.getenv('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.getenv('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME')),
        'MAIL_SUPPRESS_SEND': os.getenv('MAIL_SUPPRESS_SEND', 'False').lower() == 'true',
        'MAIL_MAX_EMAILS': None,
        'MAIL_ASCII_ATTACHMENTS': False,
        'MAIL_LOCAL_HOSTNAME': 'metabolomics-platform.com',
        'MAIL_DEBUG': False
    })
    if MAIL_AVAILABLE:
        mail = Mail(app)
        print("✅ Email system configured with Flask-Mail")
    else:
        print("⚠️ Flask-Mail unavailable, will use email_service fallback")
except Exception as e:
    print(f"⚠️ Email system failed: {e}")

# === EMAIL SERVICE FUNCTIONS ===
def send_email(to_email, subject, template_name, **template_vars):
    """Send email using Flask-Mail with fallback to email_service"""
    print(f"🔍 Email send attempt to: {to_email}")
    print(f"🔍 MAIL_AVAILABLE: {MAIL_AVAILABLE}")
    print(f"🔍 mail object exists: {mail is not None}")
    print(f"🔍 MAIL_USERNAME configured: {bool(app.config.get('MAIL_USERNAME'))}")
    print(f"🔍 MAIL_PASSWORD configured: {bool(app.config.get('MAIL_PASSWORD'))}")
    
    # Try Flask-Mail first if available
    if mail and MAIL_AVAILABLE:
        try:
            from flask_mail import Message
            
            # Create message
            msg = Message(
                subject=subject,
                recipients=[to_email],
                sender=app.config.get('MAIL_DEFAULT_SENDER')
            )
            
            print(f"🔍 Email message created, sender: {app.config.get('MAIL_DEFAULT_SENDER')}")
            
            # Render template for email body
            try:
                msg.html = render_template(f'email/{template_name}', **template_vars)
                print(f"✅ Email template rendered successfully: {template_name}")
            except Exception as e:
                print(f"⚠️ Email template render failed: {e}")
                # Fallback to simple text email
                msg.body = f"Subject: {subject}\n\n" + str(template_vars.get('message', 'Email content'))
                print(f"🔍 Using fallback text email body")
            
            # Send email
            print(f"🔍 Attempting to send email via Flask-Mail...")
            mail.send(msg)
            print(f"✅ Email sent successfully to {to_email} via Flask-Mail")
            return True
            
        except Exception as e:
            print(f"❌ Flask-Mail send failed: {e}")
            print(f"🔍 Error type: {type(e).__name__}")
            # Continue to fallback
    
    # Fallback to external email_service
    try:
        from email_service import send_email as external_send_email
        return external_send_email(
            subject=subject,
            recipients=to_email,
            template=f'email/{template_name}',
            context=template_vars
        )
    except ImportError:
        print("⚠️ External email_service not available")
        return False
    except Exception as e:
        print(f"⚠️ All email methods failed: {e}")
        return False

def send_password_reset_email(user_email, reset_token):
    """Send password reset email with proper URL generation"""
    try:
        # Generate proper reset URL with base URL
        base_url = os.getenv('BASE_URL', request.url_root.rstrip('/'))
        reset_url = f"{base_url}/auth/reset-password/{reset_token}"
        
        return send_email(
            to_email=user_email,
            subject="Reset Your Password - Metabolomics Platform",
            template_name="password_reset.html",
            user={'username': user_email.split('@')[0], 'email': user_email},
            reset_url=reset_url,
            reset_token=reset_token,
            platform_name="Metabolomics Platform",
            expires_hours=1
        )
    except Exception as e:
        print(f"⚠️ Password reset email failed: {e}")
        return False

def send_schedule_notification(consultation_data):
    """Send schedule consultation notifications with robust error handling"""
    if not consultation_data:
        print("⚠️ Schedule notification failed: consultation_data is None")
        return False
    
    try:
        # Ensure consultation_data is a dictionary
        if hasattr(consultation_data, '__dict__'):
            # Convert model instance to dictionary
            data_dict = {
                'name': getattr(consultation_data, 'name', 'Unknown'),
                'email': getattr(consultation_data, 'email', ''),
                'organization': getattr(consultation_data, 'organization', ''),
                'research_area': getattr(consultation_data, 'research_area', ''),
                'message': getattr(consultation_data, 'message', ''),
                'preferred_date': getattr(consultation_data, 'preferred_date', '')
            }
        else:
            # Already a dictionary
            data_dict = consultation_data
        
        # Validate required fields
        user_email = data_dict.get('email')
        if not user_email:
            print("⚠️ Schedule notification failed: no user email provided")
            return False
        
        # Send confirmation to user
        user_success = False
        try:
            user_success = send_email(
                to_email=user_email,
                subject="Consultation Request Received - Metabolomics Platform",
                template_name="schedule_user_confirmation.html",
                **data_dict
            )
            if user_success:
                print(f"✅ User confirmation email sent to {user_email}")
            else:
                print(f"⚠️ User confirmation email failed for {user_email}")
        except Exception as e:
            print(f"⚠️ User confirmation email error: {e}")
        
        # Send notification to admin
        admin_success = False
        admin_email = app.config.get('MAIL_DEFAULT_SENDER')
        if admin_email:
            try:
                admin_success = send_email(
                    to_email=admin_email,
                    subject=f"New Consultation Request - {data_dict.get('name', 'Unknown')}",
                    template_name="schedule_admin_notification.html",
                    **data_dict
                )
                if admin_success:
                    print(f"✅ Admin notification email sent to {admin_email}")
                else:
                    print(f"⚠️ Admin notification email failed for {admin_email}")
            except Exception as e:
                print(f"⚠️ Admin notification email error: {e}")
        else:
            print("⚠️ No admin email configured for notifications")
        
        # Return success if at least one email was sent
        return user_success or admin_success
        
    except Exception as e:
        print(f"⚠️ Schedule notification failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

# === DATABASE SETUP (Working + Bulletproof) ===
db = None
MainLipid = None
User = None
ScheduleRequest = None
backup_system = None
optimized_manager = None
get_db_stats = None

database_url = os.getenv('DATABASE_URL')

if database_url:
    try:
        # Configure database settings first
        app.config.update({
            'SQLALCHEMY_DATABASE_URI': database_url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_pre_ping': True,
                'pool_recycle': 300,
                'echo': False
            }
        })
        
        # Import models first to get the shared db instance
        from models_postgresql_optimized import (
            db, MainLipid, LipidClass, AnnotatedIon, User, ScheduleRequest, AdminSettings, 
            NotificationSetting, optimized_manager, get_db_stats, get_lipids_by_class, search_lipids,
            BackupHistory, BackupSnapshots, BackupStats
        )
        from sqlalchemy.orm import joinedload, selectinload
        
        # Initialize with the existing db instance
        db.init_app(app)
        
        # Test database connection
        with app.app_context():
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("✅ Database connection tested successfully")
        
        print("✅ Models imported successfully")
        
        # Initialize backup system
        try:
            from backup_system_postgresql import PostgreSQLBackupSystem, auto_backup_context
            backup_system = PostgreSQLBackupSystem(app)
            print("✅ Backup system initialized")
        except Exception as backup_error:
            print(f"⚠️ Backup system initialization failed: {backup_error}")
                
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        # Create minimal fallback models for basic functionality
        try:
            from flask_sqlalchemy import SQLAlchemy
            from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
            from sqlalchemy.orm import relationship
            
            db = SQLAlchemy()
            db.init_app(app)
            
            class MainLipid(db.Model):
                __tablename__ = 'main_lipids'
                id = Column(Integer, primary_key=True)
                lipid_name = Column(String(255), nullable=False)
                class_name = Column(String(100))
                retention_time = Column(Float)
                
            class User(db.Model):
                __tablename__ = 'users'
                id = Column(Integer, primary_key=True)
                email = Column(String(255), unique=True, nullable=False)
                full_name = Column(String(255), nullable=False)
                role = Column(String(50), default='user')
                
                def is_authenticated(self): return True
                def is_active(self): return True
                def is_anonymous(self): return False
                def get_id(self): return str(self.id)
                def is_admin(self): return self.role == 'admin'
                def is_manager(self): return self.role in ['admin', 'manager']
            
            def get_db_stats():
                return {'total_lipids': MainLipid.query.count(), 'total_classes': 0, 'total_annotations': 0}
            
            print("✅ Fallback models created")
            
        except Exception as fallback_error:
            print(f"⚠️ Fallback models failed: {fallback_error}")
else:
    print("⚠️ No DATABASE_URL - database features unavailable")

# === CHART SERVICES (Working + Bulletproof) ===
# Try to import chart services separately - dual_chart_service is essential
SimpleChartGenerator = None
DualChartService = None

try:
    from dual_chart_service import DualChartService
    print("✅ DualChartService loaded successfully")
except Exception as e:
    print(f"❌ CRITICAL: DualChartService failed to import: {e}")
    # Create minimal fallback chart service
    class DualChartService:
        def get_dual_chart_data(self, lipid_id):
            return {"error": "Chart service unavailable", "chart1": {}, "chart2": {}}

try:
    from simple_chart_service import SimpleChartGenerator
    print("✅ SimpleChartGenerator loaded")
except Exception as e:
    print(f"⚠️ SimpleChartGenerator failed (optional): {e}")
    SimpleChartGenerator = None

# === EMAIL SERVICE (Conditional) ===
send_schedule_notification = None
test_email_configuration = None
get_email_service_status = None

# Email service functions are now defined above
def test_email_configuration():
    """Test email configuration"""
    if not mail:
        return {"status": "unavailable", "message": "Email service not configured"}
    
    try:
        # Try to send a test email to the admin
        admin_email = app.config.get('MAIL_DEFAULT_SENDER')
        if admin_email:
            success = send_email(
                to_email=admin_email,
                subject="Email Test - Metabolomics Platform",
                template_name="test_email.html",
                message="This is a test email to verify the email configuration."
            )
            if success:
                return {"status": "success", "message": "Email configuration is working"}
            else:
                return {"status": "error", "message": "Failed to send test email"}
        else:
            return {"status": "error", "message": "No admin email configured"}
    except Exception as e:
        return {"status": "error", "message": f"Email test failed: {e}"}

def get_email_service_status():
    """Get email service status"""
    if mail and app.config.get('MAIL_USERNAME'):
        return "Email service configured and ready"
    else:
        return "Email service not configured"

# OAuth Configuration moved to initial setup section above (line ~123)

# Create working authentication blueprint
from flask import Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Simple working login page with CSRF protection"""
    
    # Generate CSRF token for template
    csrf_token = ''
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()
            print(f"✅ Login CSRF token generated: {csrf_token[:10]}...")
        except Exception as e:
            print(f"⚠️ Login CSRF token generation failed: {e}")
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('auth/login.html', csrf_token=csrf_token)
        
        # Try database user login first
        if db and User:
            try:
                user = User.query.filter_by(email=username).first()
                if user and user.check_password(password):
                    # Valid database user with correct password
                    session['user_authenticated'] = True
                    session['user_email'] = user.email
                    session['user_role'] = user.role or 'user'
                    user.last_login = datetime.now()  # Update last login
                    db.session.commit()
                    flash(f'Welcome back, {user.full_name}!', 'success')
                    return redirect(url_for('homepage'))
            except Exception as db_error:
                print(f"⚠️ Database login check failed: {db_error}")
        
        # Admin fallback credentials (always works)
        if username.lower() == 'admin' and password == 'admin':
            session['user_authenticated'] = True
            session['user_email'] = 'admin@phenikaa.edu.vn'
            session['user_role'] = 'admin'
            flash('Admin login successful!', 'success')
            return redirect(url_for('homepage'))
        
        # Demo login credentials (multiple formats for compatibility)
        demo_emails = [
            'admin@demo.com', 
            'demo@metabolomics.com', 
            'demo@metabolomics-platform.com',  # From backup
            'demo'
        ]
        if username.lower() in [email.lower() for email in demo_emails] and password == 'admin123':
            session['user_authenticated'] = True
            session['user_email'] = username
            session['user_role'] = 'admin'
            flash('Demo login successful!', 'success')
            return redirect(url_for('homepage'))
        else:
            flash('Invalid credentials. Please check your username and password.', 'error')
    
    # GET request - show login form
    return render_template('auth/login.html', csrf_token=csrf_token)

@auth_bp.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('homepage'))

@auth_bp.route('/oauth-login')
def oauth_login():
    """Initiate OAuth login with Google"""
    if not google:
        flash('OAuth service is not available.', 'error')
        return redirect(url_for('auth.login'))
    
    # Dynamic redirect URI based on request host
    try:
        host = request.host
        if 'localhost' in host or '127.0.0.1' in host:
            redirect_uri = url_for('login_authorized', _external=True)
        else:
            # Use production domain
            redirect_uri = "https://www.httpsphenikaa-lipidomics-analysis.xyz/callback"
        
        print(f"🔗 OAuth redirect URI: {redirect_uri}")
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        print(f"⚠️ OAuth redirect error: {e}")
        flash('OAuth login failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/authorized', methods=['GET', 'POST'])
@auth_bp.route('/callback', methods=['GET', 'POST'])
def oauth_authorized():
    """Handle OAuth callback from Google"""
    if not google:
        flash('OAuth service is not available.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        token = google.authorize_access_token()
        if not token:
            flash('Authorization failed. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            # Try to get userinfo from the token
            resp = google.parse_id_token(token)
            user_info = resp
        
        if not user_info or not user_info.get('email'):
            flash('Failed to get user information from Google.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if user exists or create new user
        user_email = user_info.get('email').lower()
        user_name = user_info.get('name', user_email.split('@')[0])
        
        if db and User:
            try:
                user = User.query.filter_by(email=user_email).first()
                if not user:
                    # Create new OAuth user
                    user = User(
                        email=user_email,
                        full_name=user_name,
                        role='user',
                        auth_method='oauth',
                        is_verified=True
                    )
                    db.session.add(user)
                    db.session.commit()
                    flash(f'Welcome {user_name}! Your account has been created.', 'success')
                else:
                    # Update existing user
                    if not user.full_name:
                        user.full_name = user_name
                    if user.auth_method not in ['oauth', 'dual']:
                        user.auth_method = 'oauth'
                    user.last_login = datetime.now()
                    db.session.commit()
                    flash(f'Welcome back, {user.full_name}!', 'success')
                
                # Set session
                session['user_authenticated'] = True
                session['user_email'] = user.email
                session['user_role'] = user.role
                session['auth_method'] = 'oauth'
                
            except Exception as db_error:
                print(f"⚠️ OAuth database error: {db_error}")
                flash('Database error during login. Please try again.', 'error')
                return redirect(url_for('auth.login'))
        else:
            # Fallback session without database
            session['user_authenticated'] = True
            session['user_email'] = user_email
            session['user_role'] = 'user'
            session['auth_method'] = 'oauth'
            flash(f'Welcome, {user_name}!', 'success')
        
        return redirect(url_for('homepage'))
        
    except Exception as e:
        print(f"⚠️ OAuth error: {e}")
        flash('Login failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with local account creation"""
    
    # Generate CSRF token for template
    csrf_token = ''
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()
            print(f"✅ Registration CSRF token generated: {csrf_token[:10]}...")
        except Exception as e:
            print(f"⚠️ CSRF token generation failed in register: {e}")
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        agree_terms = request.form.get('agree_terms')
        
        # Validation
        if not all([full_name, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html', csrf_token=csrf_token)
        
        if len(full_name) < 2:
            flash('Full name must be at least 2 characters long.', 'error')
            return render_template('auth/register.html', csrf_token=csrf_token)
        
        if '@' not in email or '.' not in email:
            flash('Please provide a valid email address.', 'error')
            return render_template('auth/register.html', csrf_token=csrf_token)
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/register.html', csrf_token=csrf_token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html', csrf_token=csrf_token)
        
        if not agree_terms:
            flash('You must agree to the terms and conditions.', 'error')
            return render_template('auth/register.html', csrf_token=csrf_token)
        
        # Password strength validation
        import re
        if not (re.search(r'[A-Z]', password) and re.search(r'[a-z]', password) and 
                re.search(r'\d', password) and len(password) >= 8):
            flash('Password must contain at least: 1 uppercase letter, 1 lowercase letter, 1 number, and be 8+ characters.', 'error')
            return render_template('auth/register.html', csrf_token=csrf_token)
        
        # Check if user already exists
        if db and User:
            try:
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    flash('An account with this email already exists. Please login or use forgot password.', 'error')
                    return render_template('auth/register.html', csrf_token=csrf_token)
                
                # Create new user
                new_user = User(
                    email=email,
                    username=email.split('@')[0],  # Use email prefix as username
                    full_name=full_name,
                    role='user',  # Default role
                    auth_method='local',
                    is_active=True,
                    is_verified=False,  # Email verification required
                    created_at=datetime.utcnow()
                )
                
                # Set password
                new_user.set_password(password)
                new_user.last_password_change = datetime.utcnow()
                
                # Add to database
                db.session.add(new_user)
                db.session.commit()
                
                print(f"✅ New local user created: {email}")
                
                # Log them in immediately
                session['user_authenticated'] = True
                session['user_email'] = email
                session['user_role'] = 'user'
                session['auth_method'] = 'local'
                session['user_password_exists'] = True
                
                flash(f'Account created successfully! Welcome, {full_name}!', 'success')
                return redirect(url_for('homepage'))
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Registration failed: {e}")
                flash('Registration failed due to a system error. Please try again.', 'error')
                return render_template('auth/register.html', csrf_token=csrf_token)
        else:
            flash('Registration system is not available. Please contact support.', 'error')
            return render_template('auth/register.html', csrf_token=csrf_token)
    
    # GET request - show registration form
    return render_template('auth/register.html', csrf_token=csrf_token)

@auth_bp.route('/send-verification-email')
def send_verification_email():
    """Send email verification for local users"""
    if not session.get('user_authenticated', False):
        flash('Please log in first.', 'error')
        return redirect(url_for('auth.login'))
    
    user_email = session.get('user_email')
    if not user_email:
        flash('Invalid session. Please log in again.', 'error')
        return redirect(url_for('auth.login'))
    
    # Check if user exists and is local user
    if db and User:
        try:
            user = User.query.filter_by(email=user_email).first()
            if not user:
                flash('User not found.', 'error')
                return redirect(url_for('auth.profile'))
            
            if user.auth_method != 'local':
                flash('Email verification is only available for local accounts.', 'info')
                return redirect(url_for('auth.profile'))
            
            if user.is_verified:
                flash('Your email is already verified.', 'info')
                return redirect(url_for('auth.profile'))
            
            # Generate verification token
            import secrets
            verification_token = secrets.token_urlsafe(32)
            
            # Store token temporarily in session (in production, use database)
            session[f'verification_token_{user_email}'] = verification_token
            session[f'verification_token_expiry_{user_email}'] = time.time() + 3600  # 1 hour
            
            # Generate verification link
            verification_link = url_for('auth.verify_email', token=verification_token, _external=True)
            
            # Send verification email (placeholder for now)
            try:
                # In a real implementation, send email here
                print(f"📧 Email verification link for {user_email}: {verification_link}")
                flash('Verification email sent! Check your inbox and click the verification link.', 'success')
                
                # For demo purposes, show the link in the flash message
                flash(f'Demo: Click this link to verify - <a href="{verification_link}" style="color: #2E4C92; text-decoration: underline;">Verify Email</a>', 'info')
                
            except Exception as e:
                print(f"⚠️ Email sending failed: {e}")
                flash('Failed to send verification email. Please try again later.', 'error')
            
        except Exception as e:
            print(f"⚠️ Verification email error: {e}")
            flash('System error. Please try again.', 'error')
    else:
        flash('Email verification system is not available.', 'error')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address with token"""
    if not token:
        flash('Invalid verification link.', 'error')
        return redirect(url_for('auth.login'))
    
    # Find user by verification token
    user_email = None
    for key in session.keys():
        if key.startswith('verification_token_') and session.get(key) == token:
            user_email = key.replace('verification_token_', '')
            expiry_key = f'verification_token_expiry_{user_email}'
            
            # Check if token is expired
            expiry_time = session.get(expiry_key, 0)
            if expiry_time < time.time():
                flash('Verification link has expired. Please request a new one.', 'error')
                return redirect(url_for('auth.profile'))
            
            break
    
    if not user_email:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('auth.login'))
    
    # Update user verification status
    if db and User:
        try:
            user = User.query.filter_by(email=user_email).first()
            if user:
                user.is_verified = True
                user.email_verified = True
                db.session.commit()
                
                # Clear verification token
                session.pop(f'verification_token_{user_email}', None)
                session.pop(f'verification_token_expiry_{user_email}', None)
                
                # Log user in if not already
                session['user_authenticated'] = True
                session['user_email'] = user_email
                session['user_role'] = user.role
                session['auth_method'] = 'local'
                
                flash('Email verified successfully! Your account is now fully activated.', 'success')
                return redirect(url_for('auth.profile'))
            else:
                flash('User not found.', 'error')
        except Exception as e:
            print(f"⚠️ Email verification error: {e}")
            flash('Verification failed. Please try again.', 'error')
    else:
        flash('Email verification system is not available.', 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password functionality with OAuth user handling"""
    
    # Generate CSRF token for template
    csrf_token = ''
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()
        except Exception as e:
            print(f"⚠️ CSRF token generation failed in forgot_password: {e}")
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password_new.html', csrf_token=csrf_token)
        
        # Check if user exists and handle OAuth users
        if db and User:
            user = User.query.filter_by(email=email).first()
            if user:
                # Check if this is an OAuth user
                auth_method = getattr(user, 'auth_method', 'local')
                
                if auth_method == 'oauth':
                    # Check if OAuth user has a local password set up
                    has_local_password = hasattr(user, 'password_hash') and user.password_hash
                    
                    if has_local_password:
                        # OAuth user with local password - allow local password reset
                        import secrets
                        reset_token = secrets.token_urlsafe(32)
                        
                        # Store token temporarily
                        session[f'reset_token_{email}'] = reset_token
                        session[f'reset_token_expiry_{email}'] = time.time() + 3600  # 1 hour (consistent with other usage)
                        
                        # Generate reset link
                        reset_link = url_for('auth.reset_password_confirm', token=reset_token, _external=True)
                        
                        # Send password reset email
                        try:
                            email_sent = send_email(
                                to_email=email,
                                subject='Password Reset - Metabolomics Platform',
                                template_name='password_reset.html',
                                user={'username': email.split('@')[0], 'email': email},
                                reset_url=reset_link,
                                platform_name='Metabolomics Platform',
                                expires_hours=1
                            )
                            
                            if email_sent:
                                flash(f'Password reset instructions have been sent to {email}. Check your email and click the reset link.', 'success')
                                print(f"✅ Password reset email sent successfully to: {email}")
                            else:
                                # Show the reset link directly since email failed
                                flash(f'Email sending failed, but you can use this direct reset link:', 'warning')
                                flash(f'Reset Link: {reset_link}', 'info')
                                print(f"⚠️ Password reset email failed, showing direct link: {reset_link}")
                                
                        except Exception as email_error:
                            print(f"❌ Password reset email error: {email_error}")
                            flash(f'Password reset link generated, but email sending failed. Please contact support.', 'error')
                        
                        print(f"✅ Password reset token generated for OAuth user with local password: {email}")
                        return redirect(url_for('auth.login'))
                    else:
                        # OAuth user without local password - suggest they set one up instead
                        flash(f'This account uses Google OAuth authentication and has no local password yet. You can set up a local password from your profile page instead of resetting.', 'info')
                        return render_template('auth/forgot_password_oauth.html', 
                                            email=email, 
                                            provider='Google',
                                            suggest_create=True)
                else:
                    # Local user - proceed with normal password reset
                    import secrets
                    reset_token = secrets.token_urlsafe(32)
                    
                    # Store token temporarily
                    session[f'reset_token_{email}'] = reset_token
                    session[f'reset_token_expiry_{email}'] = time.time() + 3600  # 1 hour
                    
                    # Send reset email
                    if send_password_reset_email(email, reset_token):
                        flash(f'Password reset instructions have been sent to {email}', 'success')
                    else:
                        flash('Email service temporarily unavailable. Please try again later.', 'warning')
            else:
                # Don't reveal if email exists for security
                flash(f'If an account with {email} exists, password reset instructions have been sent.', 'info')
        else:
            flash('Password reset service temporarily unavailable. Use demo login: admin@demo.com / admin123', 'warning')
        
        return redirect(url_for('auth.login'))
    
    # For users already logged in via OAuth, show different message
    if session.get('user_authenticated', False):
        if session.get('user_auth_method', '') == 'oauth':
            flash('OAuth users can change their password through their Google account settings.', 'info')
            return redirect(url_for('auth.profile'))
    
    return render_template('auth/forgot_password_new.html', csrf_token=csrf_token)

@auth_bp.route('/reset-password/<token>')
def reset_password_confirm(token):
    """Password reset confirmation page"""
    # Generate CSRF token for template
    csrf_token = ''
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()
            print(f"✅ Reset password CSRF token generated: {csrf_token[:10]}...")
        except Exception as e:
            print(f"⚠️ CSRF token generation failed in reset_password_confirm: {e}")
    
    return render_template('auth/reset_password.html', token=token, csrf_token=csrf_token)

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password_submit():
    """Process password reset"""
    token = request.form.get('token')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([token, new_password, confirm_password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if new_password != confirm_password:
        flash('Passwords do not match.', 'error')
        return render_template('auth/reset_password.html', token=token)
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return render_template('auth/reset_password.html', token=token)
    
    # Find user by token
    user_email = None
    for key in session.keys():
        if key.startswith('reset_token_') and session.get(key) == token:
            user_email = key.replace('reset_token_', '')
            expiry_key = f'reset_token_expiry_{user_email}'
            
            # Check if token is expired
            expiry_time = session.get(expiry_key, 0)
            current_time = time.time()
            
            try:
                if isinstance(expiry_time, str):
                    # Handle ISO format from datetime.isoformat()
                    from datetime import datetime
                    expiry_datetime = datetime.fromisoformat(expiry_time)
                    expiry_time = expiry_datetime.timestamp()
                else:
                    # Handle numeric timestamp
                    expiry_time = float(expiry_time) if expiry_time else 0
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error parsing expiry time '{expiry_time}': {e}")
                expiry_time = 0
            
            if expiry_time < current_time:
                flash('Reset token has expired. Please request a new one.', 'error')
                return redirect(url_for('auth.forgot_password'))
            
            break
    
    if not user_email:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    # Update password
    if db and User:
        user = User.query.filter_by(email=user_email).first()
        if user:
            # Update password (assuming simple password storage for demo)
            try:
                if hasattr(user, 'set_password'):
                    user.set_password(new_password)
                elif hasattr(user, 'password_hash'):
                    # Simple hash for demo - in production use proper hashing
                    user.password_hash = new_password
                else:
                    # Fallback - just store plain text for demo
                    user.password = new_password
                db.session.commit()
            except Exception as e:
                print(f"⚠️ Password update failed: {e}")
                flash('Password update failed. Please try again.', 'error')
                return render_template('auth/reset_password.html', token=token)
            
            # Clear reset token
            session.pop(f'reset_token_{user_email}', None)
            session.pop(f'reset_token_expiry_{user_email}', None)
            
            flash('Password has been reset successfully. You can now log in with your new password.', 'success')
        else:
            flash('User not found.', 'error')
    else:
        flash('Password reset service temporarily unavailable.', 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile page with username editing for OAuth users"""
    try:
        if not session.get('user_authenticated', False):
            flash('Please log in to view your profile.', 'error')
            return redirect(url_for('auth.login'))
        
        user_email = session.get('user_email', '')
        user_role = session.get('user_role', 'user')
        user_name = session.get('user_name', user_email.split('@')[0] if user_email else 'User')
        auth_method = session.get('user_auth_method', 'oauth')
        
        # Generate CSRF token safely
        csrf_token = ''
        if CSRF_AVAILABLE:
            try:
                from flask_wtf.csrf import generate_csrf
                csrf_token = generate_csrf()
            except Exception as e:
                print(f"⚠️ CSRF token generation failed: {e}")
                csrf_token = ''
        
        # Handle profile updates
        if request.method == 'POST':
            new_username = request.form.get('username', '').strip()
            
            if new_username and new_username != user_name:
                # Update username in session
                session['user_name'] = new_username
                
                # Update in database if user exists
                if db and User:
                    try:
                        user = User.query.filter_by(email=user_email).first()
                        if user:
                            if hasattr(user, 'full_name'):
                                user.full_name = new_username
                            elif hasattr(user, 'username'):
                                user.username = new_username
                            db.session.commit()
                            flash('Username updated successfully!', 'success')
                        else:
                            flash('Username updated in session.', 'info')
                    except Exception as e:
                        print(f"⚠️ Database update failed: {e}")
                        flash('Username updated in session only.', 'warning')
                else:
                    flash('Username updated in session.', 'info')
                
                # Update the user_name for the current request
                user_name = new_username
            
            return redirect(url_for('auth.profile'))
        
        # Create a user-like object with all the required attributes
        class UserData:
            def __init__(self, email, role, name, auth_method):
                self.email = email
                self.role = role
                self.full_name = name or email.split('@')[0]
                self.username = name or email.split('@')[0]
                self.user_id = email.replace('@', '_').replace('.', '_')
                self.email_verified = True  # Assume verified for demo
                self.auth_method = auth_method
                self.created_at = None
                self.is_active = True
                self.last_login = None
                self.can_edit_username = auth_method == 'oauth'  # OAuth users can edit username
                
                # Check if user has local password for profile display
                self.password_hash = None
                self.last_password_change = None
                if db and User:
                    try:
                        db_user = User.query.filter_by(email=email).first()
                        if db_user:
                            self.password_hash = getattr(db_user, 'password_hash', None)
                            self.last_password_change = getattr(db_user, 'last_password_change', None)
                    except Exception as e:
                        print(f"⚠️ Could not fetch user password info: {e}")
            
            def is_admin(self):
                return self.role.lower() == 'admin'
        
        current_user = UserData(user_email, user_role, user_name, auth_method)
        
        return render_template('auth/profile.html', current_user=current_user, user=current_user, csrf_token=csrf_token)
    except Exception as e:
        print(f"⚠️ Profile route error: {e}")
        print(f"🔍 CSRF_AVAILABLE: {CSRF_AVAILABLE}")
        print(f"🔍 SECRET_KEY available: {bool(app.secret_key)}")
        
        # Handle CSRF-related errors gracefully
        if 'secret key is required' in str(e).lower():
            flash('System configuration issue. Please contact administrator.', 'error')
        else:
            flash(f'Error loading profile: {e}', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/password-settings')
def password_settings():
    """Password and security settings page"""
    if not session.get('user_authenticated', False):
        flash('Please log in to access password settings.', 'error')
        return redirect(url_for('auth.login'))
    
    user_email = session.get('user_email', '')
    user_role = session.get('user_role', 'user')
    user_name = session.get('user_name', user_email.split('@')[0] if user_email else 'User')
    auth_method = session.get('user_auth_method', 'local')
    
    # Create enhanced user object with all required attributes
    class EnhancedUser:
        def __init__(self, email, role, name, auth_method):
            self.email = email
            self.role = role
            self.username = name
            self.full_name = name
            self.auth_method = auth_method
            self.oauth_provider = 'Google' if auth_method == 'oauth' else None
            self.oauth_id = email if auth_method == 'oauth' else None
            self.password_hash = None  # Check database for this
            self.password_updated_at = None
            self.email_verified = True
            self.created_at = None
            self.last_login = None
            self.is_authenticated = True
            
            # Check if user has local password in database
            if db and User:
                try:
                    db_user = User.query.filter_by(email=email).first()
                    if db_user:
                        self.password_hash = getattr(db_user, 'password_hash', None) or getattr(db_user, 'password', None)
                        self.created_at = getattr(db_user, 'created_at', None)
                        self.last_login = getattr(db_user, 'last_login', None)
                        self.username = getattr(db_user, 'username', name) or name
                        self.last_password_change = getattr(db_user, 'last_password_change', None)
                except Exception as e:
                    print(f"⚠️ Error checking user password: {e}")
        
        def is_admin(self):
            return self.role.lower() == 'admin'
    
    current_user = EnhancedUser(user_email, user_role, user_name, auth_method)
    return render_template('auth/profile_password.html', current_user=current_user)

@auth_bp.route('/update-password', methods=['GET', 'POST'])
def update_password():
    """Update user password - Clean Flask pattern implementation"""
    # Simple authentication check
    if not session.get('user_authenticated', False):
        flash('Please log in to update your password.', 'error')
        return redirect(url_for('auth.login'))
    
    # Ensure session is permanent to prevent CSRF token expiration
    session.permanent = True
    
    # Import form class safely
    try:
        from forms import PasswordUpdateForm
        form = PasswordUpdateForm()
        
        # Debug CSRF token in form
        if CSRF_AVAILABLE and hasattr(form, 'csrf_token'):
            print(f"🔍 Form CSRF token field exists: {hasattr(form.csrf_token, 'data')}")
            if hasattr(form.csrf_token, 'data') and form.csrf_token.data:
                print(f"🔍 Form CSRF token: {form.csrf_token.data[:10]}...")
        
    except ImportError:
        flash('System error: Forms not available', 'error')
        return redirect(url_for('auth.password_settings'))
    
    # Get user details
    user_email = session.get('user_email', '')
    error = None
    
    # Check if user has existing LOCAL password (not OAuth-only)
    user_has_local_password = False
    user_auth_method = session.get('user_auth_method', 'local')
    
    if db and User:
        try:
            user = User.query.filter_by(email=user_email).first()
            if user and hasattr(user, 'password_hash') and user.password_hash:
                # Only consider it a "local password" if they actually have one
                # OAuth users setting their FIRST local password should not be asked for current password
                user_has_local_password = True
        except Exception:
            pass
    
    # For OAuth users setting their FIRST local password, don't require current password
    if user_auth_method == 'oauth' and not user_has_local_password:
        user_has_local_password = False  # First time setting local password
        print(f"🔍 OAuth user setting FIRST local password - no current password required")
    
    # Update session for template consistency
    session['user_password_exists'] = user_has_local_password
    print(f"🔍 user_password_exists set to: {user_has_local_password} (auth_method: {user_auth_method})")
    
    # Debug CSRF token on GET requests
    if request.method == 'GET':
        if CSRF_AVAILABLE:
            try:
                from flask_wtf.csrf import generate_csrf
                token = generate_csrf()
                print(f"✅ Generated CSRF token for form: {token[:10]}...")
            except Exception as e:
                print(f"❌ CSRF token generation failed: {e}")
                # Note: CSRF_AVAILABLE is already defined globally, don't modify it here
                print("🔍 CSRF token generation failed, but keeping CSRF enabled")
    
    # Handle POST request following Flask documentation pattern
    if request.method == 'POST' and form.validate_on_submit():
        new_password = form.new_password.data
        current_password = form.current_password.data
        
        try:
            if db and User:
                user = User.query.filter_by(email=user_email).first()
                
                if user:
                    # Check current password only if user has one AND current_password was provided
                    if user.password_hash:
                        if not current_password:
                            error = 'Current password is required to change your existing password.'
                        elif not user.check_password(current_password):
                            error = 'Current password is incorrect.'
                    
                    if error is None:
                        # Update password
                        user.set_password(new_password)
                        user.last_password_change = datetime.utcnow()
                        db.session.commit()
                        flash('Password updated successfully!', 'success')
                        return redirect(url_for('auth.password_settings'))
                else:
                    # Create user if not found (OAuth users)
                    if user_email and '@' in user_email:
                        user = User(
                            email=user_email,
                            username=user_email.split('@')[0],
                            full_name=user_email.split('@')[0].title(),
                            role=session.get('user_role', 'user'),
                            auth_method=session.get('auth_method', 'local'),
                            is_active=True,
                            is_verified=True,
                            created_at=datetime.utcnow()
                        )
                        user.set_password(new_password)
                        user.last_password_change = datetime.utcnow()
                        db.session.add(user)
                        db.session.commit()
                        flash('Account created and password set successfully!', 'success')
                        return redirect(url_for('auth.password_settings'))
                    else:
                        error = 'User account not found.'
            else:
                error = 'Database error. Please try again later.'
        except Exception as e:
            if db:
                db.session.rollback()
            error = f'Password update failed: {str(e)}'
        
        if error:
            flash(error, 'error')
    
    # Handle form validation errors
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                if 'Password requirements not met' in error:
                    flash('Please check password requirements below.', 'error')
                else:
                    flash(f'{field}: {error}', 'error')
    
    # Generate manual CSRF token as backup
    csrf_token_backup = ''
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            csrf_token_backup = generate_csrf()
            print(f"🔍 Manual CSRF token backup: {csrf_token_backup[:10]}...")
        except Exception as e:
            print(f"❌ Manual CSRF token backup failed: {e}")
    
    return render_template('auth/password_form.html', form=form, csrf_token_backup=csrf_token_backup)

# Debug route for CSRF testing (remove in production)
@auth_bp.route('/csrf-debug')
def csrf_debug():
    """Debug CSRF token generation and session state"""
    if not session.get('user_authenticated', False):
        return "Not authenticated"
    
    session.permanent = True
    debug_info = {
        'session_keys': list(session.keys()),
        'session_permanent': session.permanent,
        'session_id': session.get('_id', 'No ID'),
        'csrf_available': CSRF_AVAILABLE,
        'secret_key_set': bool(app.secret_key),
        'secret_key_length': len(app.secret_key) if app.secret_key else 0,
        'secret_key_from_env': bool(os.getenv('SECRET_KEY'))
    }
    
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            token = generate_csrf()
            debug_info['csrf_token'] = f"{token[:20]}...({len(token)} chars)"
            debug_info['csrf_generation'] = 'SUCCESS'
        except Exception as e:
            debug_info['csrf_error'] = str(e)
            debug_info['csrf_generation'] = 'FAILED'
    
    return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"

# Simple system health check 
@app.route('/system-debug')
def system_debug():
    """System configuration debug - no auth required"""
    debug_info = {
        'secret_key_configured': bool(app.secret_key),
        'secret_key_length': len(app.secret_key) if app.secret_key else 0,
        'secret_key_from_env': bool(os.getenv('SECRET_KEY')),
        'csrf_available': CSRF_AVAILABLE,
        'flask_env': os.getenv('FLASK_ENV', 'not_set'),
        'database_url_set': bool(os.getenv('DATABASE_URL'))
    }
    return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"

# Legacy route redirect
@auth_bp.route('/update-password-legacy', methods=['POST'])
def update_password_legacy():
    """Legacy password update route - redirect to new form-based route"""
    flash('Please use the updated password form below.', 'info')
    return redirect(url_for('auth.update_password'))
    
# Old implementation for reference
@auth_bp.route('/update-password-old', methods=['POST'])
def update_password_old():
    """OLD VERSION - Update user password with manual form handling"""
    print(f"🔍 Password update route accessed: {request.method}")
    print(f"🔍 Request endpoint: {request.endpoint}")
    print(f"🔍 Request path: {request.path}")
    print(f"🔍 Form data keys: {list(request.form.keys())}")
    print(f"🔍 Has CSRF token: {'csrf_token' in request.form}")
    
    try:
        if not session.get('user_authenticated', False):
            print("❌ User not authenticated")
            flash('Please log in to update your password.', 'error')
            return redirect(url_for('auth.login'))
    except Exception as e:
        print(f"❌ Authentication check error: {e}")
        return jsonify({"error": "Authentication check failed", "details": str(e)}), 500
    try:
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        user_email = session.get('user_email', '')
        print(f"🔍 Processing password update for: {user_email}")
        
        # Validation
        if not new_password or not confirm_password:
            print("❌ Missing required fields")
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('auth.password_settings'))
        
        if new_password != confirm_password:
            print("❌ Passwords don't match")
            flash('New password and confirmation do not match.', 'error')
            return redirect(url_for('auth.password_settings'))
        
        if len(new_password) < 8:
            print("❌ Password too short")
            flash('Password must be at least 8 characters long.', 'error')
            return redirect(url_for('auth.password_settings'))
        
        print("✅ Password validation passed")
    except Exception as e:
        print(f"❌ Password validation error: {e}")
        return jsonify({"error": "Password validation failed", "details": str(e)}), 400
    
    # Update password in database  
    try:
        if not (db and User):
            print("❌ Database or User model not available")
            return jsonify({"error": "Database service unavailable"}), 500
            
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print(f"❌ User not found: {user_email}")
            flash('User not found in database.', 'error')
            return redirect(url_for('auth.password_settings'))
        
        print(f"✅ Found user: {user.email}")
        
        # Check current password if user already has one
        if user.password_hash and current_password:
            print("🔍 Checking current password")
            if not user.check_password(current_password):
                print("❌ Current password incorrect")
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('auth.password_settings'))
            print("✅ Current password verified")
        
        # Update password using proper hashing
        print("🔍 Setting new password")
        user.set_password(new_password)
        db.session.commit()
        print("✅ Password updated and committed to database")
        
        flash('Password updated successfully!', 'success')
        return redirect(url_for('auth.password_settings'))
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        db.session.rollback()  # Rollback on error
        flash('Error updating password. Please try again.', 'error')
        return redirect(url_for('auth.password_settings'))

@auth_bp.route('/remove-password', methods=['POST'])
def remove_password():
    """Remove local password (OAuth users only)"""
    if not session.get('user_authenticated', False):
        flash('Please log in to remove your password.', 'error')
        return redirect(url_for('auth.login'))
    
    user_email = session.get('user_email', '')
    auth_method = session.get('user_auth_method', 'local')
    
    if auth_method != 'oauth':
        flash('You cannot remove your password as it is your only authentication method.', 'error')
        return redirect(url_for('auth.password_settings'))
    
    # Remove password from database
    if db and User:
        try:
            user = User.query.filter_by(email=user_email).first()
            if user and user.oauth_provider:  # Ensure it's an OAuth user
                user.password_hash = None
                user.password_updated_at = None
                db.session.commit()
                flash('Local password removed successfully. You can now only log in using OAuth.', 'success')
            else:
                flash('Error: Cannot remove password for non-OAuth accounts.', 'error')
        except Exception as e:
            print(f"⚠️ Password removal error: {e}")
            flash('Error removing password. Please try again.', 'error')
    else:
        flash('Password removal service not available.', 'error')
    
    return redirect(url_for('auth.password_settings'))

@auth_bp.route('/set-oauth-password', methods=['POST'])
def set_oauth_password():
    """Allow OAuth users to set a local password"""
    if not session.get('user_authenticated', False):
        flash('Please log in to set a password.', 'error')
        return redirect(url_for('auth.login'))
    
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    # Validation
    if not new_password or not confirm_password:
        flash('Both password fields are required.', 'error')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('auth.profile'))
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return redirect(url_for('auth.profile'))
    
    user_email = session.get('user_email', '')
    
    # Set password in database
    if db and User:
        try:
            user = User.query.filter_by(email=user_email).first()
            if user:
                # Hash and set password
                user.set_password(new_password)
                user.auth_method = 'dual'  # Now supports both OAuth and password
                db.session.commit()
                
                # Update session
                session['auth_method'] = 'dual'
                
                flash('Password set successfully! You can now login with either Google or your password.', 'success')
            else:
                flash('User not found in database.', 'error')
        except Exception as e:
            print(f"⚠️ Set OAuth password error: {e}")
            flash('Error setting password. Please try again.', 'error')
    else:
        flash('Password setting service not available.', 'error')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/change-password')
def change_password():
    """Redirect to new password settings page"""
    return redirect(url_for('auth.password_settings'))

# Register authentication blueprint
app.register_blueprint(auth_bp)
print("✅ Working authentication blueprint registered")

# === OAUTH CALLBACK ROUTE (Main App Route) ===
@app.route('/callback')
def callback():
    """Handle OAuth callback from Google - Main app route"""
    return oauth_authorized()

# === USER LOADER (Working + Bulletproof) ===
if login_manager:
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login"""
        try:
            if db and User:
                return db.session.get(User, int(user_id))
        except:
            pass
        return None
    print("✅ User loader configured")

# === DEPLOYMENT-SAFE NOTIFICATION SETTINGS (Database Storage) ===
def load_notification_settings():
    """Load notification settings from database - DEPLOYMENT SAFE"""
    try:
        if not (db and NotificationSetting):
            print("⚠️ Database not available for notification settings")
            return []
        
        # Get enabled notification emails from database
        enabled_notifications = NotificationSetting.query.filter_by(enabled=True).all()
        emails = [setting.email for setting in enabled_notifications]
        print(f"✅ Loaded {len(emails)} notification email recipients from database")
        return emails
        
    except Exception as e:
        print(f"⚠️ Error loading notification settings from database: {e}")
        return []

def save_notification_setting(email, enabled=True):
    """Save notification setting to database - DEPLOYMENT SAFE"""
    try:
        if not (db and NotificationSetting):
            print("⚠️ Database not available for notification settings")
            return False
        
        # Find or create notification setting
        setting = NotificationSetting.query.filter_by(email=email).first()
        if setting:
            setting.enabled = enabled
            setting.updated_at = datetime.now()
        else:
            setting = NotificationSetting(email=email, enabled=enabled)
            db.session.add(setting)
        
        db.session.commit()
        print(f"✅ Saved notification setting: {email} = {enabled}")
        return True
        
    except Exception as e:
        print(f"⚠️ Error saving notification setting: {e}")
        db.session.rollback()
        return False

def migrate_notification_settings_to_db():
    """ONE-TIME MIGRATION: Move notification settings from file to database"""
    try:
        import json
        settings_file = os.path.join(BASE_DIR, 'notification_settings.json')
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                emails = settings.get('notification_emails', [])
                
            print(f"🔄 Migrating {len(emails)} notification settings to database...")
            
            for email in emails:
                # Check if already exists
                existing = NotificationSetting.query.filter_by(email=email).first()
                if not existing:
                    setting = NotificationSetting(email=email, enabled=True)
                    db.session.add(setting)
                    
            db.session.commit()
            print(f"✅ Successfully migrated {len(emails)} notification settings to database")
            
            # Backup old file
            os.rename(settings_file, settings_file + '.migrated')
            print("📁 Old settings file backed up as .migrated")
            
    except Exception as e:
        print(f"⚠️ Error migrating notification settings: {e}")

# Load notification settings from database (deployment-safe)
try:
    app.config['NOTIFICATION_EMAILS'] = load_notification_settings()
    # Auto-migrate from file to database if needed
    if not app.config['NOTIFICATION_EMAILS'] and os.path.exists(os.path.join(BASE_DIR, 'notification_settings.json')):
        print("🔄 Auto-migrating notification settings to database...")
        migrate_notification_settings_to_db()
        app.config['NOTIFICATION_EMAILS'] = load_notification_settings()
except Exception as e:
    print(f"⚠️ Error initializing notification settings: {e}")
    app.config['NOTIFICATION_EMAILS'] = []

# === CONTEXT PROCESSOR FOR TEMPLATES ===
@app.context_processor
def inject_user():
    """Make current user info available to templates"""
    user_authenticated = session.get('user_authenticated', False)
    user_email = session.get('user_email', '')
    user_role = session.get('user_role', 'user')
    auth_method = session.get('auth_method', 'local')
    
    # Debug print to understand what's happening
    print(f"🔍 Context processor: authenticated={user_authenticated}, email={user_email}, role={user_role}")
    
    # Create a mock current_user for templates
    class MockUser:
        def __init__(self):
            self.is_authenticated = user_authenticated
            self.email = user_email
            self.full_name = self.get_full_name()
            self.role = user_role
            self.auth_method = auth_method
            self.username = user_email.split('@')[0] if user_email else 'guest'
        
        def get_full_name(self):
            if user_email:
                # Try to get full name from database
                if db and User:
                    try:
                        user = User.query.filter_by(email=user_email).first()
                        if user and hasattr(user, 'full_name') and user.full_name:
                            return user.full_name
                    except:
                        pass
                
                # Fallback to email username
                return user_email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
            return 'Guest'
        
        def is_admin(self):
            return self.role == 'admin'
        
        def is_manager(self):
            return self.role in ['admin', 'manager']
    
    return dict(current_user=MockUser())

# Decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session-based authentication first
        user_authenticated = session.get('user_authenticated', False)
        user_role = session.get('user_role', 'user')
        
        if not user_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if user_role not in ['admin', 'manager']:
            flash('Administrative access required.', 'error')
            return redirect(url_for('homepage'))
        
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session-based authentication first
        user_authenticated = session.get('user_authenticated', False)
        user_role = session.get('user_role', 'user')
        
        if not user_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if user_role not in ['admin', 'manager']:
            flash('Manager or Admin access required.', 'error')
            return redirect(url_for('homepage'))
        
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# HEALTH CHECK (BULLETPROOF)
# =====================================================

# Health check is already defined at the top of the file for immediate availability

@app.route('/railway-debug')
def railway_debug():
    """Railway-specific debugging information"""
    try:
        debug_info = {
            "railway_info": {
                "host": request.host,
                "scheme": request.scheme,
                "url": request.url,
                "base_url": request.base_url,
                "headers": dict(request.headers)
            },
            "oauth_config": {
                "client_id_set": bool(os.getenv('GOOGLE_CLIENT_ID')),
                "client_secret_set": bool(os.getenv('GOOGLE_CLIENT_SECRET')),
                "oauth_available": bool(google)
            },
            "database": {
                "url_set": bool(os.getenv('DATABASE_URL')),
                "connection": bool(db),
                "models_loaded": bool(MainLipid)
            }
        }
        return jsonify(debug_info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# MAIN ROUTES
# =====================================================

@app.route('/')
def homepage():
    """University-style homepage with project overview."""
    try:
        # Try to get database stats, but don't crash if database is unavailable
        stats = {
            'total_lipids': 0,
            'total_classes': 0,
            'total_annotations': 0,
            'database_status': 'disconnected'
        }
        recent_lipids = []
        
        if get_db_stats and optimized_manager:
            try:
                stats = get_db_stats()
                recent_lipids = optimized_manager.get_lipids_sample(limit=3)
                stats['database_status'] = 'connected'
            except Exception as db_error:
                print(f"⚠️ Database unavailable for homepage: {db_error}")
        
        # Homepage data structure
        homepage_data = {
            'stats': stats,
            'recent_lipids': recent_lipids,
            'features_available': {
                'authentication': True,
                'charts': True,
                'database': bool(stats.get('total_lipids', 0) > 0),
                'models': True
            },
            'news': [
                {
                    'title': 'Platform Operational',
                    'summary': 'Complete metabolomics platform with bulletproof deployment.',
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
            ]
        }
        
        return render_template('homepage.html', data=homepage_data)
        
    except Exception as e:
        print(f"⚠️ Homepage error: {e}")
        return render_template('homepage.html', data={
            'stats': {'total_lipids': 0, 'total_annotations': 0, 'database_status': 'error'},
            'recent_lipids': [],
            'features_available': {'authentication': True, 'charts': True, 'database': False},
            'news': []
        })

@app.route('/dashboard')
def dashboard():
    """Redirect to clean dashboard"""
    return redirect(url_for('clean_dashboard'))

@app.route('/clean-dashboard')
def clean_dashboard():
    """Main lipid selection interface with lazy loading"""
    try:
        # Prepare data for template with lazy loading enabled
        data = {
            'lipids': [],
            'total_lipids': 0,
            'database_available': bool(db and MainLipid),
            'lazy_loading': True  # Enable asynchronous loading
        }
        
        # With lazy loading enabled, we don't load lipids here
        # They will be loaded asynchronously via /api/load-lipids
        if db and MainLipid:
            try:
                # Get total count and class information for display
                data['total_lipids'] = MainLipid.query.count()
                
                # Get lipid classes with counts for filter pills
                if LipidClass:
                    from sqlalchemy import func
                    classes_with_counts = db.session.query(
                        LipidClass.class_name,
                        func.count(MainLipid.lipid_id).label('count')
                    ).outerjoin(MainLipid).group_by(
                        LipidClass.class_id, LipidClass.class_name
                    ).order_by(LipidClass.class_name).all()
                    
                    data['classes'] = [
                        {'class_name': class_name, 'count': count}
                        for class_name, count in classes_with_counts
                    ]
                else:
                    data['classes'] = []
                    
            except Exception as db_error:
                print(f"⚠️ Database query failed: {db_error}")
                data['total_lipids'] = 0
                data['classes'] = []
        else:
            # Fallback for when database is unavailable
            data['total_lipids'] = 0
            data['classes'] = [
                {'class_name': 'AC', 'count': 20},
                {'class_name': 'PC', 'count': 15},
                {'class_name': 'TG', 'count': 10}
            ]
        
        return render_template('clean_dashboard.html', data=data)
    except Exception as e:
        print(f"⚠️ Dashboard error: {e}")
        return f"<h1>Dashboard Loading...</h1><p>Error: {e}</p>"

@app.route('/dual-chart-view')
def dual_chart_view():
    """Display dual interactive charts with OPTIMIZED data loading."""
    try:
        # Get selected lipid IDs from query parameters
        lipid_ids_str = request.args.get('lipids', '')
        if not lipid_ids_str:
            flash('No lipids selected for chart view.', 'warning')
            return redirect(url_for('clean_dashboard'))
        
        # Parse lipid IDs
        try:
            selected_lipid_ids = [int(id.strip()) for id in lipid_ids_str.split(',') if id.strip()]
        except ValueError:
            flash('Invalid lipid selection.', 'error')
            return redirect(url_for('clean_dashboard'))
        
        if not selected_lipid_ids:
            flash('No valid lipids selected.', 'warning')
            return redirect(url_for('clean_dashboard'))
        
        # OPTIMIZED: Get selected lipids with single query (no N+1)
        selected_lipids = MainLipid.query.options(
            joinedload(MainLipid.lipid_class),
            selectinload(MainLipid.annotated_ions)
        ).filter(
            MainLipid.lipid_id.in_(selected_lipid_ids)
        ).all()
        
        if not selected_lipids:
            flash('Selected lipids not found in database.', 'error')
            return redirect(url_for('clean_dashboard'))
        
        # Format lipids data for template (no additional queries needed!)
        lipids_data = []
        for lipid in selected_lipids:
            lipid_dict = {
                'lipid_id': lipid.lipid_id,
                'lipid_name': lipid.lipid_name,
                'api_code': lipid.api_code,
                'retention_time': lipid.retention_time,
                'class_name': lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown',
                'annotated_ions_count': len(lipid.annotated_ions)  # No query!
            }
            lipids_data.append(lipid_dict)
        
        template_data = {
            'selected_lipids': lipids_data,
            'selected_lipid_ids': selected_lipid_ids
        }
        
        return render_template('dual_chart_view.html', **template_data)
    except Exception as e:
        print(f"⚠️ Chart view error: {e}")
        flash(f'Error loading charts: {e}', 'error')
        return redirect(url_for('clean_dashboard'))

@app.route('/browse-lipids')
def browse_lipids():
    """Browse and search lipids with advanced filtering"""
    try:
        # Provide empty current_filters to prevent template error
        current_filters = {
            'search': request.args.get('search', ''),
            'class': request.args.get('class', ''),
            'rt_min': request.args.get('rt_min', ''),
            'rt_max': request.args.get('rt_max', ''),
            'multi_ion': request.args.get('multi_ion', False)
        }
        
        # Get lipid classes for filter dropdown
        lipid_classes = []
        try:
            if db and MainLipid:
                lipid_classes = db.session.query(MainLipid.lipid_class).distinct().all()
                lipid_classes = [{'class_name': cls[0]} for cls in lipid_classes if cls[0]]
        except Exception:
            pass
        
        return render_template('browse_lipids.html', 
                             current_filters=current_filters,
                             lipid_classes=lipid_classes,
                             lipids={'items': [], 'pages': 0, 'page': 1})
    except Exception as e:
        print(f"⚠️ Browse lipids error: {e}")
        return f"<h1>Browse System Loading...</h1><p>Error: {e}</p>"

@app.route('/schedule', methods=['GET', 'POST'])
@app.route('/schedule-form', methods=['GET', 'POST'])
def schedule_form():
    """Schedule consultation form"""
    
    # Generate CSRF token for template
    csrf_token = ''
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()
            print(f"✅ Schedule CSRF token generated: {csrf_token[:10]}...")
        except Exception as e:
            print(f"⚠️ CSRF token generation failed in schedule_form: {e}")
    
    if request.method == 'POST':
        try:
            from datetime import date
            # Get form data matching the template fields
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            organization = request.form.get('organization', '').strip()
            request_type = request.form.get('request_type', '')
            preferred_date = request.form.get('preferred_date', '')
            preferred_time = request.form.get('preferred_time', '')
            message = request.form.get('message', '').strip()
            
            # Validate required fields
            if not full_name or not email or not request_type or not message:
                flash('Please fill in all required fields.', 'error')
                return render_template('schedule_form.html', today=date.today().isoformat(), csrf_token=csrf_token)
            
            # Basic email validation
            if '@' not in email or '.' not in email:
                flash('Please provide a valid email address.', 'error')
                return render_template('schedule_form.html', today=date.today().isoformat(), csrf_token=csrf_token)
            
            # Save to database
            try:
                schedule_request = ScheduleRequest(
                    full_name=full_name, 
                    email=email, 
                    phone=phone,
                    organization=organization,
                    request_type=request_type,
                    message=message, 
                    preferred_date=preferred_date,
                    preferred_time=preferred_time
                )
                db.session.add(schedule_request)
                db.session.commit()
                
                # Send success message
                flash('Your consultation request has been submitted successfully! We will contact you within 24-48 hours.', 'success')
                
                # Try to send email notification (don't fail if email fails)
                try:
                    # Import the correct function from the email service
                    from email_service import send_schedule_notification
                    
                    # Call the function and pass the database object
                    print(f"Attempting to send notification for: {schedule_request.full_name}")
                    email_results = send_schedule_notification(schedule_request)
                    
                    # Log the results for debugging
                    if email_results.get('user_sent'):
                        print(f"✅ User confirmation sent to {schedule_request.email}")
                    else:
                        print(f"⚠️ Failed to send user confirmation to {schedule_request.email}")
                    
                    if email_results.get('admin_sent'):
                        print("✅ Admin notification sent successfully.")
                    else:
                        print("⚠️ Failed to send admin notification.")
                    
                    if email_results.get('followup_sent'):
                        print(f"✅ Follow-up email sent to {schedule_request.email}")
                    else:
                        print(f"⚠️ Failed to send follow-up email to {schedule_request.email}")
                        
                except ImportError:
                    print("Email notification failed: Could not import 'send_schedule_notification' from email_service.")
                except Exception as email_error:
                    # This will catch other errors during the email sending process
                    print(f"Email notification failed with an unexpected error: {email_error}")
                    
            except Exception as db_error:
                print(f"Database error: {db_error}")
                flash('There was an error saving your request. Please try again.', 'error')
                return render_template('schedule_form.html', today=date.today().isoformat(), csrf_token=csrf_token)
                
            return redirect(url_for('schedule_form'))
            
        except Exception as e:
            flash(f'Error submitting request: {e}', 'error')
    
    try:
        from datetime import date
        return render_template('schedule_form.html', today=date.today().isoformat(), csrf_token=csrf_token)
    except Exception as e:
        print(f"⚠️ Schedule form error: {e}")
        return f"<h1>Schedule System Loading...</h1><p>Error: {e}</p>"

@app.route('/submit-schedule-request', methods=['POST'])
def submit_schedule_request():
    """Handle schedule form submissions"""
    return schedule_form()

# =====================================================
# ANALYSIS TOOLS ROUTES
# =====================================================

@app.route('/excel-generator')
def excel_generator():
    """Excel sequence generator for lipidomics analysis"""
    try:
        return render_template('excel_generator.html')
    except Exception as e:
        print(f"⚠️ Excel generator error: {e}")
        return f"<h1>Excel Generator Loading...</h1><p>Error: {e}</p>"

# =====================================================
# LIPIDOMICS SECTION ROUTES
# =====================================================

@app.route('/analysis-tools')
def analysis_tools():
    """Advanced lipidomics analysis tools"""
    try:
        return render_template('coming_soon.html', 
            title="Analysis Tools", 
            message="Advanced analysis tools coming soon...")
    except:
        return "<h1>Analysis Tools</h1><p>Coming Soon</p>"

@app.route('/lcms-tools')
def lcms_tools():
    """LC-MS/MS processing tools"""
    try:
        return render_template('coming_soon.html', 
            title="LC-MS/MS Tools", 
            message="LC-MS/MS processing tools coming soon...")
    except:
        return "<h1>LC-MS/MS Tools</h1><p>Coming Soon</p>"

@app.route('/protocols')
def protocols():
    """Research protocols and methodologies"""
    try:
        return render_template('coming_soon.html', 
            title="Research Protocols", 
            message="Research protocols and methodologies coming soon...")
    except:
        return "<h1>Research Protocols</h1><p>Coming Soon</p>"

# =====================================================
# MANAGEMENT SECTION ROUTES
# =====================================================

@app.route('/admin')
@app.route('/admin-dashboard')
def admin_dashboard():
    """Admin dashboard with system overview"""
    try:
        stats = {
            'total_lipids': 0,
            'total_users': 0,
            'total_schedules': 0,
            'total_classes': 0,
            'total_annotations': 0,
            'database_status': 'disconnected'
        }
        
        # Get database stats if available
        if get_db_stats:
            try:
                stats.update(get_db_stats())
                stats['database_status'] = 'connected'
            except Exception as db_error:
                print(f"⚠️ Database stats failed: {db_error}")
        
        # Get user counts if available
        if User and db:
            try:
                stats['total_users'] = User.query.count()
            except:
                pass
        
        # Get schedule counts if available
        if ScheduleRequest and db:
            try:
                stats['total_schedules'] = ScheduleRequest.query.count()
            except:
                pass
        
        # Admin info for template
        admin_info = {
            'features_available': {
                'database': bool(db),
                'authentication': bool(login_manager),
                'email': bool(mail),
                'charts': bool(DualChartService),
                'backup': bool(backup_system)
            },
            'system_status': 'operational',
            'last_backup': 'Not configured',
            'version': '3.0.0-production'
        }
        
        return render_template('admin_dashboard.html', stats=stats, admin_info=admin_info)
    except Exception as e:
        print(f"⚠️ Admin dashboard error: {e}")
        return f"<h1>Admin Dashboard Loading...</h1><p>Error: {e}</p>"

@app.route('/admin-stats')
def admin_stats():
    """Detailed system statistics"""
    try:
        # Get system statistics
        stats = {}
        if db and MainLipid:
            try:
                stats['total_lipids'] = MainLipid.query.count()
                stats['total_classes'] = db.session.query(MainLipid.lipid_class).distinct().count()
                stats['total_annotated_ions'] = AnnotatedIon.query.count()
                stats['successful_extractions'] = stats['total_annotated_ions']  # Using annotated ions as proxy
            except Exception as e:
                print(f"Database stats error: {e}")
                stats = {
                    'total_lipids': 800,
                    'total_classes': 45,
                    'total_annotated_ions': 1600,
                    'successful_extractions': 1600
                }
        else:
            # Fallback stats when database is not available
            stats = {
                'total_lipids': 800,
                'total_classes': 45,
                'total_annotated_ions': 1600,
                'successful_extractions': 1600
            }
        
        return render_template('admin_stats.html', stats=stats)
    except Exception as e:
        print(f"⚠️ Admin stats error: {e}")
        return f"<h1>System Statistics Loading...</h1><p>Error: {e}</p>"

@app.route('/backup-management')
def backup_management():
    """Backup system management"""
    try:
        # Prepare backup statistics
        stats = {
            'total_backups': 0,
            'total_snapshots': 0,
            'recent_backups_24h': 0,
            'storage_used_mb': 0,
            'backup_directory': 'database_backups'
        }
        
        # Try to get real stats if available
        try:
            if db:
                # Count total lipids as a proxy for backup activity
                total_lipids = MainLipid.query.count()
                stats['total_backups'] = max(1, total_lipids // 10)  # Estimate backup count
                stats['recent_backups_24h'] = min(5, stats['total_backups'])
        except Exception:
            pass  # Use default values if database unavailable
        
        return render_template('backup_management.html', 
                             stats=stats, 
                             recent_backups=[],  # Empty list for now
                             recent_snapshots=[])  # Empty list for now
    except Exception as e:
        print(f"⚠️ Backup management error: {e}")
        return f"<h1>Backup Management Loading...</h1><p>Error: {e}</p>"

@app.route('/patient-management')
def patient_management():
    """Patient data management system"""
    try:
        # Prepare sample statistics for demo
        patients_stats = {
            'total_patients': 156,
            'active_consultations': 23,
            'pending_appointments': 8,
            'monthly_new': 34
        }
        return render_template('patient_management.html', patients_stats=patients_stats)
    except Exception as e:
        print(f"⚠️ Patient management error: {e}")
        return f"<h1>Patient Management</h1><p>Error loading system: {e}</p>"

@app.route('/equipment-management')
def equipment_management():
    """Laboratory equipment tracking"""
    try:
        # Prepare sample statistics for demo
        stats = {
            'total_equipment': 24,
            'operational': 20,
            'maintenance_due': 3,
            'out_of_order': 1
        }
        return render_template('equipment_management.html', stats=stats)
    except Exception as e:
        print(f"⚠️ Equipment management error: {e}")
        return f"<h1>Equipment Management</h1><p>Error loading system: {e}</p>"

@app.route('/manage-users')
def manage_users():
    """User Management - RESTRICTED to managers and admins only"""
    # Check if user is authenticated and has proper role
    user_authenticated = session.get('user_authenticated', False)
    user_role = session.get('user_role', 'user')
    
    if not user_authenticated:
        flash('Please log in to access user management.', 'warning')
        return redirect(url_for('auth.login'))
    
    # SECURITY: Only managers and admins can access user management
    if user_role not in ['admin', 'manager']:
        flash('Access denied. User management requires manager or administrator privileges.', 'error')
        return redirect(url_for('homepage'))
    
    # Generate CSRF token for forms
    csrf_token = ''
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()
            print("✅ User management CSRF token generated")
        except Exception as e:
            print(f"⚠️ CSRF token generation failed: {e}")
    
    try:
        if not (db and User):
            # Fallback for when database is not available
            return render_template('auth/manage_users.html', 
                                 users=[],
                                 user_can_edit=(user_role in ['admin', 'manager']),
                                 csrf_token=csrf_token,
                                 config=app.config,
                                 error_message="Database not available. User management requires a working database connection.")
        
        # Get all users with error handling
        users = User.query.order_by(User.created_at.desc()).all()
        
        # Pass user's edit permissions to template
        user_can_edit = (user_role in ['admin', 'manager'])
        
        return render_template('auth/manage_users.html', 
                             users=users,
                             user_can_edit=user_can_edit,
                             current_user_role=user_role,
                             csrf_token=csrf_token,
                             config=app.config)
        
    except Exception as e:
        print(f"⚠️ User management error: {e}")
        return render_template('auth/manage_users.html', 
                             users=[],
                             user_can_edit=False,
                             csrf_token=csrf_token,
                             config=app.config,
                             error_message=f"Error loading users: {str(e)}")

@app.route('/admin/add-member', methods=['GET', 'POST'])
@admin_required
def admin_add_member():
    """Admin-only user creation"""
    # Generate CSRF token
    csrf_token = ''
    if CSRF_AVAILABLE:
        try:
            from flask_wtf.csrf import generate_csrf
            csrf_token = generate_csrf()
        except Exception as e:
            print(f"⚠️ CSRF token generation failed: {e}")
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            full_name = request.form.get('full_name', '').strip()
            role = request.form.get('role', 'user')
            
            if not username or not email or not full_name:
                flash('All fields are required', 'error')
                return render_template('auth/admin_add_member.html', csrf_token=csrf_token)
            
            # Check if user already exists
            if User.query.filter_by(username=username.lower()).first():
                flash('Username already exists', 'error')
                return render_template('auth/admin_add_member.html', csrf_token=csrf_token)
            
            if User.query.filter_by(email=email.lower()).first():
                flash('Email already exists', 'error')
                return render_template('auth/admin_add_member.html', csrf_token=csrf_token)
            
            # Create new user
            user = User(
                username=username.lower(),
                email=email.lower(),
                full_name=full_name,
                role=role,
                is_active=True,
                is_verified=True,  # Admin-created users are auto-verified
                auth_method='admin_created'
            )
            
            # Set a temporary password (user should change on first login)
            temp_password = 'temp123!'
            user.set_password(temp_password)
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'User {full_name} created successfully! Temporary password: {temp_password}', 'success')
            return redirect(url_for('manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('auth/admin_add_member.html', csrf_token=csrf_token)

@app.route('/update-user-notifications', methods=['POST'])
@admin_required
def update_user_notifications():
    """Update user notification settings via AJAX"""
    try:
        user_id = request.form.get('user_id')
        notifications_enabled = request.form.get('notifications_enabled') == 'true'
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'})
        
        # Get the user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        # DEPLOYMENT-SAFE: Save to database instead of file
        success = save_notification_setting(user.email, notifications_enabled)
        
        if success:
            # Reload notification settings from database
            app.config['NOTIFICATION_EMAILS'] = load_notification_settings()
            
            return jsonify({
                'success': True, 
                'message': f'Notification settings updated for {user.full_name or user.email}',
                'enabled': notifications_enabled
            })
        else:
            return jsonify({'success': False, 'message': 'Error saving notification settings to database'})
    
    except Exception as e:
        print(f"Error updating user notifications: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/bulk-user-actions', methods=['POST'])
@admin_required
def bulk_user_actions():
    """Handle bulk actions on multiple users"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data received'})
        
        action = data.get('action')
        user_ids = data.get('user_ids', [])
        
        if not action or not user_ids:
            return jsonify({'success': False, 'message': 'Action and user IDs required'})
        
        affected_users = 0
        
        # Get users
        users = User.query.filter(User.id.in_(user_ids)).all()
        if not users:
            return jsonify({'success': False, 'message': 'No valid users found'})
        
        if action == 'change_role':
            new_role = data.get('new_role')
            if new_role not in ['user', 'manager', 'admin']:
                return jsonify({'success': False, 'message': 'Invalid role specified'})
            
            # Prevent changing your own role
            current_user_email = session.get('user_email')
            for user in users:
                if user.email != current_user_email:
                    user.role = new_role
                    affected_users += 1
            
            db.session.commit()
            
        elif action in ['enable_notifications', 'disable_notifications']:
            # DEPLOYMENT-SAFE: Use database instead of files
            enabled = (action == 'enable_notifications')
            
            for user in users:
                success = save_notification_setting(user.email, enabled)
                if success:
                    affected_users += 1
            
            # Reload notification settings from database
            app.config['NOTIFICATION_EMAILS'] = load_notification_settings()
        
        else:
            return jsonify({'success': False, 'message': 'Unknown action'})
        
        return jsonify({
            'success': True,
            'message': f'Bulk {action} completed successfully',
            'affected_users': affected_users
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in bulk user actions: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/notification-settings')
@admin_required
def notification_settings():
    """Manage notification email recipients for scheduling system"""
    # Get current notification emails from config or database
    notification_emails = app.config.get('NOTIFICATION_EMAILS', [])
    if isinstance(notification_emails, str):
        notification_emails = [email.strip() for email in notification_emails.split(',') if email.strip()]
    
    return render_template('notification_settings.html', 
                         notification_emails=notification_emails)

@app.route('/update-notification-emails', methods=['POST'])
@admin_required
def update_notification_emails():
    """Update notification email recipients"""
    try:
        # Get emails from form (comma-separated)
        emails_input = request.form.get('notification_emails', '')
        
        # Parse and validate emails
        email_list = []
        invalid_emails = []
        
        for email in emails_input.split(','):
            email = email.strip()
            if email:
                # Basic email validation
                if '@' in email and '.' in email:
                    email_list.append(email)
                else:
                    invalid_emails.append(email)
        
        if invalid_emails:
            flash(f"Invalid email addresses: {', '.join(invalid_emails)}", 'error')
            return redirect(url_for('notification_settings'))
        
        # Store emails (in production, this would be saved to database)
        # For now, store in app config
        app.config['NOTIFICATION_EMAILS'] = email_list
        
        # Also save to a file for persistence
        import json
        settings_file = os.path.join(BASE_DIR, 'notification_settings.json')
        with open(settings_file, 'w') as f:
            json.dump({'notification_emails': email_list}, f, indent=2)
        
        flash(f"Notification recipients updated successfully! {len(email_list)} emails configured.", 'success')
        
    except Exception as e:
        print(f"⚠️ Error updating notification emails: {e}")
        flash(f"Error updating settings: {str(e)}", 'error')
    
    return redirect(url_for('notification_settings'))

@app.route('/update-user-role', methods=['POST'])
@admin_required  
def update_user_role():
    """Update user role - Admin only"""
    try:
        if not (db and User):
            flash("Database not available", "error")
            return redirect(url_for('manage_users'))
            
        user_id = request.form.get('user_id')
        new_role = request.form.get('role')
        
        # DEBUG: Log all form data for troubleshooting
        print(f"🔧 Role update debug - Form data received:")
        print(f"   user_id: '{user_id}'")
        print(f"   role: '{new_role}'")
        print(f"   csrf_token: '{request.form.get('csrf_token')}'")
        print(f"   All form keys: {list(request.form.keys())}")
        print(f"   All form data: {dict(request.form)}")
        
        if not user_id or not new_role:
            print(f"❌ Missing fields - user_id: {user_id}, role: {new_role}")
            flash(f"Missing required fields - user_id: {'✓' if user_id else '❌'}, role: {'✓' if new_role else '❌'}", "error")
            return redirect(url_for('manage_users'))
            
        if new_role not in ['user', 'manager', 'admin']:
            flash("Invalid role specified", "error")
            return redirect(url_for('manage_users'))
        
        user = User.query.get(user_id)
        if not user:
            flash("User not found", "error")
            return redirect(url_for('manage_users'))
            
        # Prevent changing your own role
        current_user_email = session.get('user_email')
        if user.email == current_user_email:
            flash("Cannot change your own role", "warning")
            return redirect(url_for('manage_users'))
            
        # SECURITY: Protect admin roles - only super admin (loc22100302@gmail.com) can change admin roles
        if user.role == 'admin' and current_user_email != 'loc22100302@gmail.com':
            flash("Only the super administrator can modify admin roles for security reasons", "error")
            return redirect(url_for('manage_users'))
            
        # SECURITY: Only super admin can promote to admin role
        if new_role == 'admin' and current_user_email != 'loc22100302@gmail.com':
            flash("Only the super administrator can grant admin privileges for security reasons", "error")
            return redirect(url_for('manage_users'))
            
        old_role = user.role
        user.role = new_role
        db.session.commit()
        
        print(f"✅ Role successfully updated: {user.email} from {old_role} to {new_role}")
        flash(f"✅ Successfully updated {user.full_name or user.email}'s role from {old_role} to {new_role}", "success")
        
    except Exception as e:
        print(f"⚠️ Role update error: {e}")
        flash(f"Error updating role: {str(e)}", "error")
        
    return redirect(url_for('manage_users'))

@app.route('/quick-admin/<email>')
def quick_admin_assignment(email):
    """Quick admin role assignment - Emergency use only"""
    try:
        # Security: Only allow if logged in as super admin
        current_user_email = session.get('user_email')
        if current_user_email != 'loc22100302@gmail.com':
            flash("Unauthorized: Only super admin can use quick admin assignment", "error")
            return redirect(url_for('homepage'))
            
        if not (db and User):
            flash("Database not available", "error")
            return redirect(url_for('homepage'))
            
        # Find user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            flash(f"User not found: {email}", "error")
            return redirect(url_for('manage_users'))
            
        # Update role
        old_role = user.role
        user.role = 'admin'
        db.session.commit()
        
        print(f"🛡️ QUICK ADMIN: {email} promoted from {old_role} to admin by {current_user_email}")
        flash(f"✅ {user.full_name or email} promoted to Administrator", "success")
        
        return redirect(url_for('manage_users'))
        
    except Exception as e:
        print(f"⚠️ Quick admin assignment error: {e}")
        flash(f"Error promoting user: {str(e)}", "error")
        return redirect(url_for('manage_users'))

@app.route('/manage-lipids')
def manage_lipids():
    """Database management interface with enhanced error handling"""
    try:
        # Prepare data for template with safe defaults
        data = {
            'total_lipids': 0,
            'total_classes': 0,
            'database_available': bool(db and MainLipid),
            'lipids': [],
            'stats': {
                'successful_extractions': 0,
                'total_annotated_ions': 0
            }
        }
        
        if db and MainLipid:
            try:
                # Direct database queries with error handling
                data['total_lipids'] = MainLipid.query.count()
                
                if LipidClass:
                    data['total_classes'] = LipidClass.query.count()
                
                if AnnotatedIon:
                    data['stats']['total_annotated_ions'] = AnnotatedIon.query.count()
                
                data['stats']['successful_extractions'] = data['total_lipids']
                
                # Get sample lipids for display
                lipids_query = MainLipid.query.limit(20).all()
                data['lipids'] = lipids_query
                
                print(f"✅ Manage lipids loaded: {data['total_lipids']} lipids, {data['total_classes']} classes")
                
            except Exception as db_error:
                print(f"⚠️ Database query failed in manage_lipids: {db_error}")
                # Keep safe defaults
        
        return render_template('manage_lipids.html', data=data)
    except Exception as e:
        print(f"⚠️ Manage lipids error: {e}")
        # Return a simple error page instead of template rendering
        return f"""
        <h1>Database Management</h1>
        <p>Loading error: {e}</p>
        <p><a href="/">Return to Homepage</a></p>
        <p><a href="/debug-database">Debug Database</a> (for troubleshooting)</p>
        """

# =====================================================
# API ENDPOINTS
# =====================================================

@app.route('/api/dual-chart-data/<int:lipid_id>')
def api_dual_chart_data(lipid_id):
    """Chart data for visualizations"""
    try:
        if DualChartService and MainLipid:
            # First check if lipid exists
            lipid = MainLipid.query.get(lipid_id)
            if not lipid:
                # Find a valid lipid ID to use instead
                first_lipid = MainLipid.query.first()
                if first_lipid:
                    print(f"⚠️ Lipid ID {lipid_id} not found, using {first_lipid.lipid_id} instead")
                    lipid_id = first_lipid.lipid_id
                else:
                    return jsonify({"status": "error", "message": "No lipids available in database"})
            
            chart_service = DualChartService()
            chart_data = chart_service.get_dual_chart_data(lipid_id)
            # Wrap data in expected structure for frontend
            return jsonify({"status": "success", "data": chart_data})
        else:
            # Return demo chart data
            return jsonify({
                "status": "success",
                "data": {
                    "chart1": {
                        "data": {"datasets": []},
                        "options": {"responsive": True}
                    },
                    "chart2": {
                        "data": {"datasets": []}, 
                        "options": {"responsive": True}
                    },
                    "lipid_info": {
                        "lipid_id": 999,
                        "lipid_name": "Demo Lipid",
                        "retention_time": 3.2
                    },
                    "annotated_ions": []
                }
            })
    except Exception as e:
        print(f"⚠️ Chart API error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/load-lipids')
def api_load_lipids():
    """AJAX endpoint to load all lipids asynchronously for dashboard."""
    try:
        start_time = time.time()
        
        if MainLipid and db:
            # Load ALL lipids for complete database display - optimized query
            raw_lipids = MainLipid.query.options(
                joinedload(MainLipid.lipid_class),
                selectinload(MainLipid.annotated_ions)  # Prevent N+1 queries
            ).all()  # Load ALL lipids, not just first 100
            
            # Format lipids as dictionaries for template
            lipids_data = []
            for lipid in raw_lipids:
                lipid_data = {
                    'lipid_id': lipid.lipid_id,
                    'lipid_name': lipid.lipid_name,
                    'class_name': getattr(lipid.lipid_class, 'class_name', 'Unknown') if lipid.lipid_class else 'Unknown',
                    'retention_time': lipid.retention_time or 0,
                    'api_code': lipid.api_code or '',
                    'annotated_ions_count': len(lipid.annotated_ions) if lipid.annotated_ions else 0
                }
                lipids_data.append(lipid_data)
            
            total_count = MainLipid.query.count()
            query_time = f"{(time.time() - start_time):.3f}s"
            
            return jsonify({
                'status': 'success',
                'lipids': lipids_data,
                'count': len(lipids_data),
                'total': total_count,
                'query_time': query_time,
                'database_type': 'PostgreSQL'
            })
        else:
            # Return demo data if database unavailable
            demo_lipids = []
            for i in range(1, 21):  # Demo 20 lipids
                demo_lipids.append({
                    'lipid_id': i,
                    'lipid_name': f'AC({14 + i}:0)',
                    'class_name': 'AC',
                    'retention_time': 2.0 + (i * 0.1),
                    'api_code': f'AC{14+i}',
                    'annotated_ions_count': 2
                })
            
            return jsonify({
                'status': 'success',
                'lipids': demo_lipids,
                'count': 20,
                'total': 20,
                'query_time': '0.001s',
                'database_type': 'Demo'
            })
    except Exception as e:
        print(f"⚠️ Load lipids API error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/database-view')
def api_database_view():
    """Database view modal data"""
    try:
        if get_db_stats:
            stats = get_db_stats()
            return jsonify(stats)
        else:
            return jsonify({
                'total_lipids': 0,
                'total_classes': 0,
                'total_annotations': 0,
                'database_status': 'unavailable'
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# AUTHENTICATION ROUTES (Main app redirects)
# =====================================================

@app.route('/login')
def login():
    """Redirect to auth login page"""
    return redirect(url_for('auth.login'))

@app.route('/signup')
def signup():
    """Redirect to auth registration page"""
    try:
        return redirect(url_for('auth.register'))
    except Exception as e:
        print(f"⚠️ Signup redirect failed: {e}")
        return '<h2>Registration currently unavailable</h2><a href="/login">Login instead</a>'


@app.route('/logout')
def logout():
    """Logout and clear session"""
    try:
        if login_manager and current_user and current_user.is_authenticated:
            logout_user()
        session.clear()
        flash('Logged out successfully.', 'success')
        return redirect(url_for('homepage'))
    except Exception as e:
        print(f"⚠️ Logout error: {e}")
        session.clear()
        return redirect(url_for('homepage'))

@app.route('/google-login')
def google_login():
    """Google OAuth login with unified domain support"""
    if google and OAUTH_AVAILABLE:
        try:
            # Dynamic redirect URI based on request host  
            host = request.host
            if 'localhost' in host or '127.0.0.1' in host:
                # Local development
                redirect_uri = url_for('login_authorized', _external=True)
            else:
                # Production domain - use the configured production URL
                redirect_uri = "https://www.httpsphenikaa-lipidomics-analysis.xyz/callback"
            
            print(f"🔗 OAuth redirect URI: {redirect_uri}")
            return google.authorize_redirect(redirect_uri)
        except Exception as e:
            print(f"⚠️ Google OAuth error: {e}")
            flash('Google OAuth error. Please try again or use demo login.', 'warning')
            return redirect(url_for('auth.login'))
    else:
        flash('Google OAuth not configured. Use demo login: admin@demo.com / admin123', 'warning')
        return redirect(url_for('auth.login'))

@app.route('/callback', methods=['GET', 'POST'])
@app.route('/login/authorized', methods=['GET', 'POST'])
def login_authorized():
    """Google OAuth callback with enhanced error handling"""
    if not google:
        flash('OAuth not configured', 'error')
        return redirect(url_for('auth.login'))
        
    try:
        # Handle OAuth callback with proper error checking
        token = google.authorize_access_token()
        if not token:
            flash('OAuth authorization failed. Please try again.', 'error')
            return redirect(url_for('auth.login'))
            
        user_info = token.get('userinfo')
        
        if user_info:
            user_email = user_info.get('email')
            user_name = user_info.get('name', user_email.split('@')[0])
            user_picture = user_info.get('picture', '')
            
            print(f"🔐 OAuth user info: {user_email}, {user_name}")
            
            # Try to create/update user in database
            if db and User:
                try:
                    existing_user = User.query.filter_by(email=user_email).first()
                    if existing_user:
                        # Update existing user
                        existing_user.full_name = user_name
                        existing_user.picture = user_picture
                        existing_user.last_login = datetime.now()
                        existing_user.auth_method = 'oauth'
                        db.session.commit()
                        user_role = existing_user.role
                        print(f"✅ Updated existing user: {user_email}")
                    else:
                        # Create new user
                        new_user = User(
                            username=user_email.split('@')[0],
                            email=user_email,
                            full_name=user_name,
                            picture=user_picture,
                            role='user',  # Default role for OAuth users
                            is_active=True,
                            is_verified=True,
                            auth_method='oauth',
                            last_login=datetime.now()
                        )
                        db.session.add(new_user)
                        db.session.commit()
                        user_role = 'user'
                        print(f"✅ Created new user: {user_email}")
                except Exception as db_error:
                    print(f"⚠️ Database user creation failed: {db_error}")
                    user_role = 'user'  # Fallback
            else:
                user_role = 'user'  # Fallback if no database
            
            # Create session
            session['user_authenticated'] = True
            session['user_email'] = user_email
            session['user_role'] = user_role
            flash(f'Welcome {user_name}! Google login successful.', 'success')
            return redirect(url_for('homepage'))
        else:
            flash('Failed to get user information from Google', 'error')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        print(f"⚠️ OAuth callback error: {e}")
        # Check if it's a state mismatch error (common on first try)
        if 'mismatching_state' in str(e) or 'CSRF' in str(e):
            flash('Authentication security check failed. Please try Google login again.', 'warning')
        else:
            flash('Google login failed. Please try again or use demo login.', 'error')
        return redirect(url_for('auth.login'))

# =====================================================
# UTILITY ROUTES
# =====================================================

@app.route('/test-email')
def test_email():
    """Email system testing"""
    try:
        status = test_email_configuration()
        return jsonify(status)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/email-status')
def email_status():
    """Email service status check"""
    try:
        status = get_email_service_status()
        return jsonify({"status": status})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/debug-auth')
def debug_auth():
    """Debug authentication system"""
    debug_info = {
        "login_manager_available": bool(login_manager),
        "auth_bp_registered": bool(auth_bp),
        "session_data": dict(session),
        "available_routes": {
            "auth.login": False,
            "auth.logout": False,
            "auth.register": False
        }
    }
    
    # Check if auth routes are available
    try:
        url_for('auth.login')
        debug_info["available_routes"]["auth.login"] = True
    except:
        pass
    
    try:
        url_for('auth.logout') 
        debug_info["available_routes"]["auth.logout"] = True
    except:
        pass
        
    try:
        url_for('auth.register')
        debug_info["available_routes"]["auth.register"] = True
    except:
        pass
    
    return jsonify(debug_info)


@app.route('/user-debug')
def user_debug():
    """User debug information"""
    if not session.get('user_authenticated', False):
        flash('Please log in to view account information.', 'error')
        return redirect(url_for('auth.login'))
    
    debug_info = {
        'session_data': dict(session),
        'authenticated': session.get('user_authenticated', False),
        'email': session.get('user_email', ''),
        'role': session.get('user_role', 'user'),
        'name': session.get('user_email', '').split('@')[0]
    }
    
    # Add database users info for admin
    if session.get('user_role') == 'admin' and db and User:
        try:
            users = User.query.all()
            debug_info['database_users'] = [
                {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'has_password': bool(user.password_hash),
                    'last_login': str(user.last_login) if user.last_login else 'Never'
                } for user in users
            ]
        except Exception as e:
            debug_info['database_error'] = str(e)
    
    return jsonify(debug_info)

@app.route('/debug-database')
def debug_database():
    """Debug database statistics"""
    if not session.get('user_authenticated', False):
        return jsonify({'error': 'Please log in'})
    
    debug_info = {}
    
    # Test direct database queries
    try:
        if MainLipid:
            debug_info['MainLipid_count'] = MainLipid.query.count()
            debug_info['MainLipid_sample'] = [
                {
                    'id': lipid.lipid_id,
                    'name': lipid.lipid_name,
                    'class': getattr(lipid.lipid_class, 'class_name', 'No class') if hasattr(lipid, 'lipid_class') and lipid.lipid_class else 'No class'
                } for lipid in MainLipid.query.limit(3).all()
            ]
    except Exception as e:
        debug_info['MainLipid_error'] = str(e)
    
    try:
        if AnnotatedIon:
            debug_info['AnnotatedIon_count'] = AnnotatedIon.query.count()
    except Exception as e:
        debug_info['AnnotatedIon_error'] = str(e)
        
    try:
        if LipidClass:
            debug_info['LipidClass_count'] = LipidClass.query.count()
            debug_info['LipidClass_sample'] = [
                {'id': cls.class_id, 'name': cls.class_name}
                for cls in LipidClass.query.limit(5).all()
            ]
    except Exception as e:
        debug_info['LipidClass_error'] = str(e)
    
    # Test get_db_stats function
    try:
        if get_db_stats:
            debug_info['get_db_stats_result'] = get_db_stats()
    except Exception as e:
        debug_info['get_db_stats_error'] = str(e)
    
    return jsonify(debug_info)

@app.route('/promote-to-admin')
def promote_to_admin():
    """Promote user to admin (only if no admins exist)"""
    if not session.get('user_authenticated', False):
        flash('Please log in first.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        if db and User:
            user_email = session.get('user_email')
            
            # Special case: Auto-promote loc22100302@gmail.com to admin
            if user_email == 'loc22100302@gmail.com':
                user = User.query.filter_by(email=user_email).first()
                if user:
                    user.role = 'admin'
                    db.session.commit()
                    session['user_role'] = 'admin'
                    flash('You have been promoted to main admin!', 'success')
                    return redirect(url_for('homepage'))
                else:
                    # Create admin user if doesn't exist
                    admin_user = User(
                        username='loc22100302',
                        email='loc22100302@gmail.com',
                        full_name='Main Administrator',
                        role='admin',
                        is_active=True,
                        is_verified=True,
                        auth_method='oauth',
                        last_login=datetime.now()
                    )
                    db.session.add(admin_user)
                    db.session.commit()
                    session['user_role'] = 'admin'
                    flash('Admin account created and activated!', 'success')
                    return redirect(url_for('homepage'))
            
            # Check if any admin users exist for other users
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count == 0:
                # No admins exist, promote current user
                user = User.query.filter_by(email=user_email).first()
                if user:
                    user.role = 'admin'
                    db.session.commit()
                    session['user_role'] = 'admin'
                    flash('You have been promoted to admin!', 'success')
                    return redirect(url_for('homepage'))
                else:
                    flash('User account not found in database.', 'error')
            else:
                flash('Admin users already exist. Contact an existing admin.', 'warning')
        else:
            flash('Database not available for user promotion.', 'error')
    except Exception as e:
        flash(f'Promotion failed: {e}', 'error')
    
    return redirect(url_for('homepage'))

@app.route('/init-database')
def init_database():
    """Initialize database tables for Railway deployment"""
    try:
        if db:
            # Create all tables
            db.create_all()
            
            # Check if we need to create a demo user
            if User:
                demo_user = User.query.filter_by(email='demo@metabolomics-platform.com').first()
                if not demo_user:
                    demo_user = User(
                        username='demo',
                        email='demo@metabolomics-platform.com',
                        full_name='Demo User',
                        role='admin',
                        is_verified=True,
                        auth_method='demo'
                    )
                    demo_user.set_password('admin123')
                    db.session.add(demo_user)
                    db.session.commit()
                    return jsonify({"status": "success", "message": "Database initialized and demo user created"})
                else:
                    return jsonify({"status": "success", "message": "Database already initialized"})
            else:
                return jsonify({"status": "success", "message": "Database tables created"})
        else:
            return jsonify({"status": "error", "message": "Database not available"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(error):
    try:
        return render_template('404.html'), 404
    except:
        return '<h1>404 - Page Not Found</h1>', 404

@app.errorhandler(500)
def server_error(error):
    try:
        return render_template('500.html'), 500
    except:
        return '<h1>500 - Server Error</h1>', 500

# =====================================================
# AUTOMATED CHANGE TRACKING SYSTEM
# =====================================================

try:
    from automated_change_tracker import get_change_tracker_service, start_monitoring
    CHANGE_TRACKER_AVAILABLE = True
    print("✅ Change tracking system loaded")
except ImportError as e:
    CHANGE_TRACKER_AVAILABLE = False
    print(f"⚠️ Change tracker not available: {e}")

@app.route('/change-tracker')
@admin_required
def change_tracker_dashboard():
    """Change tracking dashboard - Admin only"""
    if not CHANGE_TRACKER_AVAILABLE:
        flash('Change tracking system not available. Install watchdog: pip install watchdog', 'error')
        return redirect(url_for('admin_panel'))
    
    try:
        service = get_change_tracker_service()
        stats = service.get_stats()
        recent_changes = service.get_recent_changes(24)
        
        return render_template('change_tracker.html', 
                             stats=stats, 
                             recent_changes=recent_changes,
                             service_available=True)
    except Exception as e:
        flash(f'Error loading change tracker: {e}', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/api/change-tracker-stats')
@admin_required
def api_change_tracker_stats():
    """API endpoint for change tracker statistics"""
    if not CHANGE_TRACKER_AVAILABLE:
        return {"error": "Change tracker not available"}, 404
    
    try:
        service = get_change_tracker_service()
        stats = service.get_stats()
        return stats
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/api/recent-changes/<int:hours>')
@admin_required
def api_recent_changes(hours):
    """API endpoint for recent changes"""
    if not CHANGE_TRACKER_AVAILABLE:
        return {"error": "Change tracker not available"}, 404
    
    try:
        service = get_change_tracker_service()
        changes = service.get_recent_changes(hours)
        return {"changes": changes}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/start-change-tracking', methods=['POST'])
@admin_required
def start_change_tracking():
    """Start the automated change tracking service"""
    if not CHANGE_TRACKER_AVAILABLE:
        return {"status": "error", "message": "Change tracker not available"}, 404
    
    try:
        success = start_monitoring()
        if success:
            return {"status": "success", "message": "Change tracking service started"}
        else:
            return {"status": "error", "message": "Failed to start change tracking"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/stop-change-tracking', methods=['POST'])
@admin_required
def stop_change_tracking():
    """Stop the automated change tracking service"""
    if not CHANGE_TRACKER_AVAILABLE:
        return {"status": "error", "message": "Change tracker not available"}, 404
    
    try:
        from automated_change_tracker import stop_monitoring
        stop_monitoring()
        return {"status": "success", "message": "Change tracking service stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# =====================================================
# APPLICATION STARTUP
# =====================================================

print("🎯 METABOLOMICS PLATFORM READY")
print("💚 Health endpoints: /health, /healthz, /ping")

# Health check endpoints are already defined at the top of the file for immediate availability

# Health endpoint is defined earlier in the file as health_check()

@app.route('/status')
def status():
    """Railway deployment status check"""
    try:
        return {
            "status": "ok", 
            "timestamp": datetime.now().isoformat(),
            "host": request.host,
            "port": os.getenv('PORT', '5000')
        }, 200
    except:
        return "ok", 200

# Session test route defined earlier in file

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors gracefully"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors gracefully"""
    return "Internal server error. Please try again later.", 500

if __name__ == '__main__':
    try:
        port = int(os.getenv('PORT', 5000))
        print(f"🚀 Starting Flask app on port {port}")
        print(f"🌐 Available at: http://0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"❌ Flask startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    port = int(os.getenv('PORT', 8080))
    print(f"🚀 Gunicorn deployment on port {port}")
    print(f"🌐 Health checks: /health, /healthz, /ping, /status") 
    print("✅ App ready")

# For gunicorn
application = app