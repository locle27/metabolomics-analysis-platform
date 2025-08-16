#!/usr/bin/env python3
"""
COMPLETE AUTHENTICATION + FIXED DATABASE
Working step by step: Database FIRST, then Authentication
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.middleware.proxy_fix import ProxyFix
from pathlib import Path
import logging
from datetime import datetime
from urllib.parse import urlparse, urljoin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask configuration
BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=BASE_DIR / "templates", static_folder=BASE_DIR / "static")

# Fix for Railway HTTPS proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
app.secret_key = os.getenv('SECRET_KEY', 'metabolomics-dev-key-change-in-production')

# =====================================================
# DATABASE INITIALIZATION - STEP BY STEP
# =====================================================

# First, let's configure the database connection
database_url = os.getenv('DATABASE_URL')
logger.info(f"Database URL: {database_url[:50]}..." if database_url else "No DATABASE_URL found")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize database components one by one
database_available = False
db = None
MainLipid = None
User = None
ScheduleRequest = None

try:
    # Step 1: Import SQLAlchemy
    from flask_sqlalchemy import SQLAlchemy
    logger.info("✅ SQLAlchemy imported")
    
    # Step 2: Create database instance
    db = SQLAlchemy()
    logger.info("✅ Database instance created")
    
    # Step 3: Initialize with app
    db.init_app(app)
    logger.info("✅ Database initialized with app")
    
    # Step 4: Import models
    from models_postgresql_optimized import MainLipid, User, ScheduleRequest, VerificationToken
    logger.info("✅ Models imported successfully")
    
    # Step 5: Create tables within app context
    with app.app_context():
        db.create_all()
        logger.info("✅ Database tables created successfully")
        
        # Step 6: Test a simple query
        lipid_count = MainLipid.query.count()
        logger.info(f"✅ Database test query successful: {lipid_count} lipids found")
        
    database_available = True
    logger.info("🎉 Database fully operational!")
    
except Exception as e:
    logger.error(f"❌ Database initialization failed at step: {str(e)}")
    logger.error(f"Error type: {type(e).__name__}")
    database_available = False

# =====================================================
# EMAIL SERVICE INITIALIZATION
# =====================================================

email_available = False
try:
    from email_service_simple import send_email, test_email_configuration, send_schedule_notification
    logger.info("✅ Email service imported successfully")
    email_available = True
except Exception as e:
    logger.error(f"❌ Email service import failed: {e}")
    email_available = False

# =====================================================
# AUTHENTICATION INITIALIZATION
# =====================================================

# Flask-Login setup
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# OAuth Configuration for Railway domain
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Authentication blueprint
auth_available = False
try:
    from email_auth_production import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    logger.info("✅ Authentication blueprint registered successfully")
    auth_available = True
except Exception as e:
    logger.error(f"❌ Authentication blueprint failed: {e}")
    auth_available = False

# User loader
@login_manager.user_loader
def load_user(user_id):
    if database_available and User:
        try:
            with app.app_context():
                return User.query.get(int(user_id))
        except Exception as e:
            logger.error(f"User loader error: {e}")
            return None
    return None

def is_safe_url(target):
    """Check if URL is safe for redirect"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# =====================================================
# MAIN ROUTES
# =====================================================

@app.route('/')
def homepage():
    """Homepage with detailed system diagnostics"""
    
    # Get detailed database diagnostics
    db_diagnostics = {
        'connected': database_available,
        'url_configured': bool(os.getenv('DATABASE_URL')),
        'tables_created': False,
        'query_working': False,
        'lipid_count': 0,
        'user_count': 0,
        'error': None
    }
    
    if database_available and db:
        try:
            with app.app_context():
                # Test table existence
                lipid_count = MainLipid.query.count()
                user_count = User.query.count()
                schedule_count = ScheduleRequest.query.count()
                
                db_diagnostics.update({
                    'tables_created': True,
                    'query_working': True,
                    'lipid_count': lipid_count,
                    'user_count': user_count,
                    'schedule_count': schedule_count
                })
                
        except Exception as e:
            db_diagnostics['error'] = str(e)
            logger.error(f"Database query failed: {e}")
    
    # System status
    systems = {
        'database': database_available,
        'email': email_available,
        'auth': auth_available
    }
    
    # User info
    user_info = None
    if current_user.is_authenticated:
        user_info = {
            'username': current_user.username,
            'email': current_user.email,
            'role': getattr(current_user, 'role', 'user'),
            'auth_method': getattr(current_user, 'auth_method', 'unknown')
        }
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Metabolomics Platform - Authentication Ready</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 20px auto; padding: 20px; }}
            .header {{ background: #2E4C92; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 30px; }}
            .status-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin: 30px 0; }}
            .status-card {{ padding: 20px; border-radius: 8px; border: 2px solid #ddd; }}
            .success {{ background: #d4edda; border-color: #28a745; }}
            .error {{ background: #f8d7da; border-color: #dc3545; }}
            .user-info {{ background: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .button {{ background: #2E4C92; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; display: inline-block; }}
            .button.google {{ background: #db4437; }}
            .button.demo {{ background: #28a745; }}
            .diagnostic {{ background: #e2e3e5; padding: 10px; border-radius: 5px; margin: 10px 0; font-family: monospace; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧬 Metabolomics Platform</h1>
            <p>Complete Authentication System | Railway Domain: httpsphenikaa-lipidomics-analysis.xyz</p>
        </div>

        {'<div class="user-info"><h3>👤 Welcome, ' + user_info["username"] + '!</h3><p>Email: ' + user_info["email"] + ' | Role: ' + user_info["role"] + ' | Method: ' + user_info["auth_method"] + '</p><a href="/dashboard" class="button">📊 Dashboard</a> <a href="/logout" class="button">🚪 Logout</a></div>' if user_info else ''}

        <div class="status-grid">
            <div class="status-card {'success' if systems['database'] else 'error'}">
                <h3>🗄️ Database System</h3>
                <p><strong>Status:</strong> {'✅ Fully Operational' if systems['database'] else '❌ Failed'}</p>
                <div class="diagnostic">
                URL Configured: {'✅' if db_diagnostics['url_configured'] else '❌'}<br>
                Connection: {'✅' if db_diagnostics['connected'] else '❌'}<br>
                Tables Created: {'✅' if db_diagnostics['tables_created'] else '❌'}<br>
                Queries Working: {'✅' if db_diagnostics['query_working'] else '❌'}<br>
                Lipids: {db_diagnostics['lipid_count']}<br>
                Users: {db_diagnostics['user_count']}<br>
                {'Error: ' + db_diagnostics['error'] if db_diagnostics['error'] else ''}
                </div>
                <a href="/test-database-detailed" class="button">🔍 Test Database</a>
            </div>
            
            <div class="status-card {'success' if systems['email'] else 'error'}">
                <h3>📧 Email System</h3>
                <p><strong>Status:</strong> {'✅ Gmail SMTP Ready' if systems['email'] else '❌ Failed'}</p>
                <p>Verified working with Railway domain</p>
                <a href="/test-email-send" class="button">📧 Send Test</a>
            </div>
            
            <div class="status-card {'success' if systems['auth'] else 'error'}">
                <h3>🔐 Authentication System</h3>
                <p><strong>Status:</strong> {'✅ Ready for Testing' if systems['auth'] else '❌ Failed'}</p>
                <p>Registration, Password Reset, Google OAuth</p>
                <a href="/test-auth-complete" class="button">🧪 Test Auth</a>
            </div>
        </div>

        {'<h2>🔐 Authentication Options</h2><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 20px 0;"><a href="/auth/register" class="button">📝 Register</a><a href="/auth/login" class="button">🔑 Login</a><a href="/google-login" class="button google">🔗 Google OAuth</a><a href="/demo-login" class="button demo">🎯 Demo Login</a></div><p style="text-align: center;"><a href="/auth/forgot-password" style="color: #2E4C92;">Forgot Password?</a></p>' if not user_info else ''}

        <h2>🧪 Complete Feature Testing</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; margin: 20px 0;">
            <a href="/test-auth-complete" class="button">🔐 Test All Auth</a>
            <a href="/test-database-detailed" class="button">🗄️ Test Database</a>
            <a href="/test-email-send" class="button">📧 Test Email</a>
            <a href="/schedule-full-test" class="button">📅 Test Schedule</a>
        </div>

        <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h3>📊 System Readiness</h3>
            <ul>
                <li>✅ Flask app running on Railway</li>
                <li>{'✅' if systems['database'] else '❌'} PostgreSQL database with data</li>
                <li>{'✅' if systems['email'] else '❌'} Gmail SMTP email service</li>
                <li>{'✅' if systems['auth'] else '❌'} Complete authentication system</li>
                <li>{'✅' if all(systems.values()) else '🔄'} Ready for production use</li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.route('/test-database-detailed')
def test_database_detailed():
    """Detailed database testing with step-by-step diagnostics"""
    if not database_available:
        return jsonify({
            'status': 'error',
            'message': 'Database not available',
            'database_url': bool(os.getenv('DATABASE_URL')),
            'error_details': 'Database initialization failed during startup'
        })
    
    try:
        with app.app_context():
            # Test 1: Basic connection
            result = {'status': 'success', 'tests': []}
            
            # Test 2: Table queries
            try:
                lipid_count = MainLipid.query.count()
                result['tests'].append({'test': 'MainLipid query', 'status': 'success', 'count': lipid_count})
            except Exception as e:
                result['tests'].append({'test': 'MainLipid query', 'status': 'error', 'error': str(e)})
            
            try:
                user_count = User.query.count()
                result['tests'].append({'test': 'User query', 'status': 'success', 'count': user_count})
            except Exception as e:
                result['tests'].append({'test': 'User query', 'status': 'error', 'error': str(e)})
            
            try:
                schedule_count = ScheduleRequest.query.count()
                result['tests'].append({'test': 'ScheduleRequest query', 'status': 'success', 'count': schedule_count})
            except Exception as e:
                result['tests'].append({'test': 'ScheduleRequest query', 'status': 'error', 'error': str(e)})
            
            # Test 3: Sample data
            try:
                sample_lipid = MainLipid.query.first()
                if sample_lipid:
                    result['sample_data'] = {
                        'lipid_name': sample_lipid.lipid_name,
                        'retention_time': sample_lipid.retention_time
                    }
                else:
                    result['sample_data'] = {'note': 'No lipids found'}
            except Exception as e:
                result['sample_data'] = {'error': str(e)}
            
            return jsonify(result)
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database test failed: {str(e)}',
            'error_type': type(e).__name__
        })

@app.route('/test-auth-complete')
def test_auth_complete():
    """Complete authentication feature testing"""
    return f"""
    <h1>🔐 Complete Authentication Testing</h1>
    <p>Domain: <strong>httpsphenikaa-lipidomics-analysis.xyz</strong></p>
    
    <h2>📝 Registration & Email Verification</h2>
    <ul>
        <li><a href="/auth/register">Create New Account</a> - Full email verification</li>
        <li>Check email for verification link</li>
        <li>Test strong password requirements</li>
    </ul>
    
    <h2>🔑 Login & Password Management</h2>
    <ul>
        <li><a href="/auth/login">Standard Login</a></li>
        <li><a href="/auth/forgot-password">Forgot Password</a> - Email reset</li>
        <li><a href="/auth/change-password">Change Password</a> (login required)</li>
    </ul>
    
    <h2>🔗 Google OAuth Integration</h2>
    <ul>
        <li><a href="/google-login">Login with Google</a></li>
        <li>Automatic account creation</li>
        <li>Profile sync from Google</li>
    </ul>
    
    <h2>🎯 Testing & Demo</h2>
    <ul>
        <li><a href="/demo-login">Demo Admin Login</a> - Instant access</li>
        <li><a href="/test-email-send">Test Email System</a></li>
    </ul>
    
    <h2>📊 System Status</h2>
    <ul>
        <li>Database: {'✅ Working' if database_available else '❌ Failed'}</li>
        <li>Email: {'✅ Working' if email_available else '❌ Failed'}</li>
        <li>Authentication: {'✅ Working' if auth_available else '❌ Failed'}</li>
    </ul>
    
    <p><a href="/">← Back to Home</a></p>
    """

# =====================================================
# AUTHENTICATION ROUTES
# =====================================================

@app.route('/demo-login')
def demo_login():
    """Demo login for testing"""
    if not database_available:
        flash('Database not available for demo login', 'error')
        return redirect(url_for('homepage'))
    
    try:
        with app.app_context():
            # Check if demo admin exists
            demo_user = User.query.filter_by(username='demo_admin').first()
            
            if not demo_user:
                # Create demo admin user
                demo_user = User(
                    username='demo_admin',
                    email='demo@metabolomics-platform.com',
                    full_name='Demo Administrator',
                    role='admin',
                    is_active=True,
                    is_verified=True,
                    auth_method='demo'
                )
                demo_user.set_password('demo123')
                db.session.add(demo_user)
                db.session.commit()
                logger.info("Demo admin user created")
            
            # Log in demo user
            login_user(demo_user)
            flash('🎯 Demo login successful! You are now logged in as admin.', 'success')
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        flash(f'Demo login failed: {str(e)}', 'error')
        return redirect(url_for('homepage'))

@app.route('/google-login')
def google_login():
    """Initiate Google OAuth login"""
    # Store the next URL in session
    session['oauth_next'] = request.args.get('next')
    
    # Railway domain redirect URI
    redirect_uri = url_for('google_callback', _external=True)
    logger.info(f"Google OAuth redirect URI: {redirect_uri}")
    
    return google.authorize_redirect(redirect_uri)

@app.route('/google-callback')
@app.route('/auth/google/callback')
@app.route('/callback')
@app.route('/auth')
def google_callback():
    """Handle Google OAuth callback"""
    if not database_available:
        flash('Database not available for OAuth', 'error')
        return redirect(url_for('homepage'))
    
    try:
        # Get token from Google
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            flash('Failed to get user information from Google', 'error')
            return redirect(url_for('homepage'))
        
        with app.app_context():
            # Check if user exists
            user = User.query.filter_by(email=user_info['email']).first()
            
            if not user:
                # Create new user from Google OAuth
                user = User(
                    username=user_info['email'].split('@')[0],
                    email=user_info['email'],
                    full_name=user_info.get('name', ''),
                    picture=user_info.get('picture', ''),
                    role='user',
                    is_active=True,
                    is_verified=True,  # Google OAuth users are pre-verified
                    auth_method='oauth'
                )
                db.session.add(user)
                db.session.commit()
                flash('Account created successfully with Google!', 'success')
            else:
                # Update existing user info
                user.full_name = user_info.get('name', user.full_name)
                user.picture = user_info.get('picture', user.picture)
                user.last_login = datetime.utcnow()
                db.session.commit()
            
            # Log in user
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = session.pop('oauth_next', None)
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        flash('OAuth login failed. Please try again.', 'error')
        return redirect(url_for('homepage'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    return f"""
    <h1>🎯 Welcome to Your Dashboard</h1>
    <p>Hello <strong>{current_user.full_name or current_user.username}</strong>!</p>
    <p>Email: {current_user.email}</p>
    <p>Role: {getattr(current_user, 'role', 'user')}</p>
    <p>Authentication Method: {getattr(current_user, 'auth_method', 'password')}</p>
    
    <h3>🔬 Available Features:</h3>
    <ul>
        <li><a href="/schedule-authenticated">Schedule Consultation</a></li>
        <li><a href="/auth/profile">Manage Profile</a></li>
        <li><a href="/auth/change-password">Change Password</a></li>
    </ul>
    
    <p><a href="/logout">Logout</a> | <a href="/">← Home</a></p>
    """

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('homepage'))

# =====================================================
# EMAIL TESTING
# =====================================================

@app.route('/test-email-send')
def test_email_send():
    """Test email sending"""
    if not email_available:
        return jsonify({'status': 'error', 'message': 'Email service not available'})
    
    try:
        result = test_email_configuration()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# =====================================================
# SCHEDULING
# =====================================================

@app.route('/schedule-full-test', methods=['GET', 'POST'])
def schedule_full_test():
    """Complete scheduling test with detailed error handling"""
    if request.method == 'POST':
        if not database_available:
            return jsonify({'status': 'error', 'message': 'Database not available'})
        
        try:
            with app.app_context():
                # Create schedule request
                schedule_request = ScheduleRequest(
                    full_name=request.form.get('name'),
                    email=request.form.get('email'),
                    phone=request.form.get('phone', ''),
                    organization=request.form.get('organization', ''),
                    request_type='consultation',
                    priority='medium',
                    meeting_type='online',
                    research_description=request.form.get('message', ''),
                    specific_goals=request.form.get('goals', ''),
                    status='pending'
                )
                
                db.session.add(schedule_request)
                db.session.commit()
                
                db_result = f"✅ Saved to database with ID #{schedule_request.id}"
                
                # Try to send email if available
                email_result = "❌ Email service not available"
                if email_available:
                    try:
                        email_response = send_schedule_notification(schedule_request)
                        admin_status = "✅ Sent" if email_response['admin_sent'] else "❌ Failed"
                        user_status = "✅ Sent" if email_response['user_sent'] else "❌ Failed"
                        email_result = f"Admin: {admin_status}, User: {user_status}"
                    except Exception as e:
                        email_result = f"❌ Email failed: {str(e)}"
                
                return f"""
                <h1>🎉 Schedule Test Results</h1>
                <p><strong>Database:</strong> {db_result}</p>
                <p><strong>Email:</strong> {email_result}</p>
                <p><a href="/">← Home</a></p>
                """
                
        except Exception as e:
            return f"""
            <h1>❌ Schedule Test Failed</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><strong>Error Type:</strong> {type(e).__name__}</p>
            <p><a href="/">← Home</a></p>
            """
    
    return """
    <h1>📅 Complete Schedule Test</h1>
    <form method="POST">
        <p><input type="text" name="name" placeholder="Your Name" required style="width:300px;padding:8px;"></p>
        <p><input type="email" name="email" placeholder="Your Email" required style="width:300px;padding:8px;"></p>
        <p><input type="tel" name="phone" placeholder="Phone" style="width:300px;padding:8px;"></p>
        <p><input type="text" name="organization" placeholder="Organization" style="width:300px;padding:8px;"></p>
        <p><textarea name="message" placeholder="Message" style="width:300px;height:80px;padding:8px;"></textarea></p>
        <p><button type="submit" style="background:#2E4C92;color:white;padding:10px 20px;border:none;border-radius:5px;">Submit Test</button></p>
    </form>
    <p><a href="/">← Home</a></p>
    """

# =====================================================
# API ROUTES
# =====================================================

@app.route('/api/database-view')
def api_database_view():
    """Database status API with detailed error handling"""
    if not database_available:
        return jsonify({
            'status': 'error', 
            'message': 'Database not available',
            'database_url_configured': bool(os.getenv('DATABASE_URL'))
        })
    
    try:
        with app.app_context():
            stats = {
                'lipids': MainLipid.query.count(),
                'users': User.query.count(),
                'schedule_requests': ScheduleRequest.query.count()
            }
            
            return jsonify({
                'status': 'success',
                'database': 'PostgreSQL',
                'statistics': stats,
                'database_url': os.getenv('DATABASE_URL', 'Not set')[:50] + '...'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error_type': type(e).__name__
        })

@app.route('/health')
def health():
    """Comprehensive health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'metabolomics-platform-auth-fixed-db',
        'systems': {
            'database': database_available,
            'email': email_available,
            'authentication': auth_available
        },
        'domain': request.host,
        'environment': os.getenv('FLASK_ENV', 'development'),
        'ready_for_production': all([database_available, email_available, auth_available])
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)