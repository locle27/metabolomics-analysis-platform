#!/usr/bin/env python3
"""
COMPLETE AUTHENTICATION VERSION
Database + Email + Registration + Password Reset + Google OAuth
All tested for Railway domain: httpsphenikaa-lipidomics-analysis.xyz
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

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email Configuration with SMTP hostname fix for Railway
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))

# Authentication Configuration
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
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

# Initialize database with error handling
database_available = False
try:
    from models_postgresql_optimized import (
        db, init_db, create_all_tables, 
        MainLipid, User, ScheduleRequest, VerificationToken
    )
    
    # Initialize the database with the app
    init_db(app)
    
    # Create tables if they don't exist
    with app.app_context():
        create_all_tables()
    
    logger.info("✅ Database initialized and tables created successfully")
    database_available = True
    
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    database_available = False

# Initialize email service
email_available = False
try:
    from email_service_simple import send_email, test_email_configuration, send_schedule_notification
    logger.info("✅ Email service imported successfully")
    email_available = True
except Exception as e:
    logger.error(f"❌ Email service import failed: {e}")
    email_available = False

# Initialize authentication blueprint
auth_available = False
try:
    from email_auth_production import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    logger.info("✅ Authentication blueprint registered successfully")
    auth_available = True
except Exception as e:
    logger.error(f"❌ Authentication blueprint failed: {e}")
    auth_available = False

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    if database_available:
        try:
            return User.query.get(int(user_id))
        except:
            return None
    return None

def is_safe_url(target):
    """Check if URL is safe for redirect"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# =====================================================
# CORE ROUTES
# =====================================================

@app.route('/')
def homepage():
    """Homepage with authentication status"""
    
    # System status checks
    systems = {
        'database': database_available,
        'email': email_available,
        'auth': auth_available
    }
    
    # Database stats
    db_stats = "Unable to connect"
    if database_available:
        try:
            with app.app_context():
                lipid_count = MainLipid.query.count()
                user_count = User.query.count()
                schedule_count = ScheduleRequest.query.count()
                db_stats = f"Lipids: {lipid_count}, Users: {user_count}, Requests: {schedule_count}"
        except Exception as e:
            db_stats = f"Connected but query failed: {str(e)}"
    
    # User status
    user_info = None
    if current_user.is_authenticated:
        user_info = {
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role if hasattr(current_user, 'role') else 'user'
        }
    
    return render_template('homepage_auth.html', 
                         systems=systems,
                         db_stats=db_stats,
                         user_info=user_info,
                         current_user=current_user)

# =====================================================
# AUTHENTICATION ROUTES
# =====================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route - redirect to auth blueprint"""
    return redirect(url_for('auth.login'))

@app.route('/register')
def register():
    """Register route - redirect to auth blueprint"""
    return redirect(url_for('auth.register'))

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('homepage'))

@app.route('/demo-login')
def demo_login():
    """Demo login for testing - creates admin user if needed"""
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
            
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('admin_dashboard'))
            
    except Exception as e:
        flash(f'Demo login failed: {str(e)}', 'error')
        return redirect(url_for('homepage'))

# =====================================================
# GOOGLE OAUTH ROUTES
# =====================================================

@app.route('/login/google')
def google_login():
    """Initiate Google OAuth login"""
    if not auth_available:
        flash('Authentication system not available', 'error')
        return redirect(url_for('homepage'))
    
    # Store the next URL in session
    session['oauth_next'] = request.args.get('next')
    
    # Railway domain redirect URI
    redirect_uri = url_for('google_callback', _external=True)
    logger.info(f"Google OAuth redirect URI: {redirect_uri}")
    
    return google.authorize_redirect(redirect_uri)

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

# =====================================================
# DASHBOARD & FEATURES
# =====================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    return f"""
    <h1>🎯 Welcome to Your Dashboard</h1>
    <p>Hello <strong>{current_user.full_name or current_user.username}</strong>!</p>
    <p>Email: {current_user.email}</p>
    <p>Role: {current_user.role}</p>
    <p>Authentication Method: {getattr(current_user, 'auth_method', 'password')}</p>
    
    <h3>🔬 Available Features:</h3>
    <ul>
        <li><a href="/lipid-selection">Lipid Analysis</a></li>
        <li><a href="/schedule-authenticated">Schedule Consultation</a></li>
        <li><a href="/auth/profile">Manage Profile</a></li>
        <li><a href="/auth/change-password">Change Password</a></li>
    </ul>
    
    <p><a href="/logout">Logout</a> | <a href="/">← Home</a></p>
    """

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        with app.app_context():
            stats = {
                'users': User.query.count(),
                'lipids': MainLipid.query.count(),
                'schedule_requests': ScheduleRequest.query.count(),
                'recent_users': User.query.order_by(User.created_at.desc()).limit(5).all()
            }
        
        return f"""
        <h1>🛠️ Admin Dashboard</h1>
        <p>Welcome, Admin <strong>{current_user.username}</strong>!</p>
        
        <h3>📊 System Statistics:</h3>
        <ul>
            <li>Total Users: {stats['users']}</li>
            <li>Total Lipids: {stats['lipids']}</li>
            <li>Schedule Requests: {stats['schedule_requests']}</li>
        </ul>
        
        <h3>🔧 Admin Tools:</h3>
        <ul>
            <li><a href="/test-email-send">Send Test Email</a></li>
            <li><a href="/manage-users">Manage Users</a></li>
            <li><a href="/api/database-view">Database Status</a></li>
        </ul>
        
        <h3>👥 Recent Users:</h3>
        <ul>
        {''.join([f'<li>{user.username} ({user.email}) - {user.role}</li>' for user in stats['recent_users']])}
        </ul>
        
        <p><a href="/dashboard">← Dashboard</a> | <a href="/">← Home</a></p>
        """
        
    except Exception as e:
        return f"<h1>❌ Admin Dashboard Error</h1><p>{str(e)}</p><p><a href='/'>← Home</a></p>"

# =====================================================
# SCHEDULING WITH AUTHENTICATION
# =====================================================

@app.route('/schedule-authenticated', methods=['GET', 'POST'])
@login_required
def schedule_authenticated():
    """Schedule consultation for authenticated users"""
    if request.method == 'POST':
        if not database_available:
            flash('Database not available', 'error')
            return redirect(url_for('dashboard'))
        
        try:
            with app.app_context():
                # Create schedule request with user info pre-filled
                schedule_request = ScheduleRequest(
                    full_name=current_user.full_name or current_user.username,
                    email=current_user.email,
                    phone=request.form.get('phone', ''),
                    organization=request.form.get('organization', ''),
                    request_type=request.form.get('request_type', 'consultation'),
                    priority=request.form.get('priority', 'medium'),
                    meeting_type=request.form.get('meeting_type', 'online'),
                    research_description=request.form.get('message', ''),
                    specific_goals=request.form.get('goals', ''),
                    status='pending'
                )
                
                db.session.add(schedule_request)
                db.session.commit()
                
                # Send email notifications
                if email_available:
                    try:
                        email_result = send_schedule_notification(schedule_request)
                        if email_result['admin_sent'] and email_result['user_sent']:
                            flash('✅ Consultation request submitted! Check your email for confirmation.', 'success')
                        else:
                            flash('✅ Request submitted, but email notifications may have failed.', 'warning')
                    except Exception as e:
                        flash('✅ Request submitted, but email notifications failed.', 'warning')
                else:
                    flash('✅ Request submitted! (Email notifications not available)', 'success')
                
                return redirect(url_for('dashboard'))
                
        except Exception as e:
            flash(f'Schedule request failed: {str(e)}', 'error')
            return redirect(url_for('dashboard'))
    
    return """
    <h1>📅 Schedule Consultation</h1>
    <p>Logged in as: <strong>{}</strong></p>
    
    <form method="POST" style="max-width: 500px;">
        <p><input type="tel" name="phone" placeholder="Phone Number (optional)" style="width:100%;padding:8px;"></p>
        <p><input type="text" name="organization" placeholder="Organization/University" style="width:100%;padding:8px;"></p>
        
        <p><select name="request_type" style="width:100%;padding:8px;">
            <option value="consultation">Research Consultation</option>
            <option value="demo">Platform Demo</option>
            <option value="collaboration">Collaboration</option>
            <option value="training">Training Session</option>
        </select></p>
        
        <p><select name="priority" style="width:100%;padding:8px;">
            <option value="medium">Normal Priority</option>
            <option value="high">High Priority</option>
            <option value="low">Low Priority</option>
        </select></p>
        
        <p><select name="meeting_type" style="width:100%;padding:8px;">
            <option value="online">Online Meeting</option>
            <option value="in_person">In-Person Meeting</option>
            <option value="phone">Phone Call</option>
        </select></p>
        
        <p><textarea name="message" placeholder="Describe your research needs" style="width:100%;height:80px;padding:8px;" required></textarea></p>
        <p><textarea name="goals" placeholder="Specific goals or objectives" style="width:100%;height:60px;padding:8px;"></textarea></p>
        
        <p><button type="submit" style="background:#2E4C92;color:white;padding:12px 24px;border:none;border-radius:5px;">Submit Request</button></p>
    </form>
    
    <p><a href="/dashboard">← Dashboard</a></p>
    """.format(current_user.full_name or current_user.username)

# =====================================================
# TESTING ROUTES
# =====================================================

@app.route('/test-complete-auth')
def test_complete_auth():
    """Test all authentication features"""
    return """
    <h1>🧪 Complete Authentication Test</h1>
    
    <h3>📝 Registration & Login:</h3>
    <ul>
        <li><a href="/auth/register">Register New Account</a></li>
        <li><a href="/auth/login">Login</a></li>
        <li><a href="/auth/forgot-password">Forgot Password</a></li>
    </ul>
    
    <h3>🔐 Google OAuth:</h3>
    <ul>
        <li><a href="/login/google">Login with Google</a></li>
    </ul>
    
    <h3>🎯 Demo & Testing:</h3>
    <ul>
        <li><a href="/demo-login">Demo Admin Login</a></li>
        <li><a href="/test-email-send">Test Email System</a></li>
    </ul>
    
    <h3>📊 System Status:</h3>
    <ul>
        <li>Database: {'✅' if database_available else '❌'}</li>
        <li>Email: {'✅' if email_available else '❌'}</li>
        <li>Authentication: {'✅' if auth_available else '❌'}</li>
    </ul>
    
    <p><a href="/">← Home</a></p>
    """

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
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(error):
    return """
    <h1>404 - Page Not Found</h1>
    <p>The requested page could not be found.</p>
    <p><a href="/">← Home</a></p>
    """, 404

@app.errorhandler(500)
def internal_error(error):
    return """
    <h1>500 - Internal Server Error</h1>
    <p>An internal server error occurred.</p>
    <p><a href="/">← Home</a></p>
    """, 500

# =====================================================
# HEALTH CHECK
# =====================================================

@app.route('/health')
def health():
    """Comprehensive health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'metabolomics-platform-complete-auth',
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