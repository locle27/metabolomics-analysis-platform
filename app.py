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
import datetime as dt
from pathlib import Path
from functools import wraps
from io import BytesIO

print("🚀 BULLETPROOF METABOLOMICS PLATFORM STARTING")
print(f"🐍 Python: {sys.version}")
print(f"📁 Directory: {os.getcwd()}")
print(f"📡 Port: {os.getenv('PORT', '5000')}")
print("=" * 60)

# === BULLETPROOF IMPORTS ===
# Core Flask (REQUIRED)
try:
    from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, send_file, session, get_flashed_messages
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

# === FLASK APP CONFIGURATION ===
BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, 
    template_folder=BASE_DIR / "templates", 
    static_folder=BASE_DIR / "static"
)
app.secret_key = os.getenv('SECRET_KEY', 'bulletproof-metabolomics-platform-secret-key')

# Enhanced session configuration for OAuth
app.config.update({
    'SESSION_COOKIE_SECURE': False,  # Allow HTTP for localhost
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hour
})

# Apply proxy fix if available
if PROXY_FIX_AVAILABLE:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
    print("✅ Railway proxy configured")

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
            
            # Render template for email body
            try:
                msg.html = render_template(f'email/{template_name}', **template_vars)
            except Exception as e:
                # Fallback to simple text email
                msg.body = f"Subject: {subject}\n\n" + str(template_vars.get('message', 'Email content'))
            
            # Send email
            mail.send(msg)
            print(f"✅ Email sent successfully to {to_email} via Flask-Mail")
            return True
            
        except Exception as e:
            print(f"⚠️ Flask-Mail send failed: {e}, trying email_service...")
    
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
            optimized_manager, get_db_stats, get_lipids_by_class, search_lipids,
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
    """Simple working login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('auth/login.html')
        
        # Try database user login first (support both email and username)
        if db and User:
            try:
                # Try to find user by email or username
                user = User.query.filter(
                    (User.email == username) | (User.username == username)
                ).first()
                
                if user:
                    # Check if account is locked
                    if user.is_account_locked():
                        flash('Account is temporarily locked due to failed login attempts. Please try again later.', 'error')
                        return render_template('auth/login.html')
                    
                    # Check password
                    if user.check_password(password):
                        # Successful login - reset failed attempts and login via Flask-Login
                        user.failed_login_attempts = 0
                        user.locked_until = None
                        user.last_login = datetime.utcnow()
                        db.session.commit()
                        
                        # Use Flask-Login for proper session management
                        login_user(user, remember=True)
                        
                        # Also set session variables for backward compatibility
                        session['user_authenticated'] = True
                        session['user_email'] = user.email
                        session['user_role'] = user.role or 'user'
                        session['user_auth_method'] = user.auth_method or 'password'
                        
                        flash(f'Welcome back, {user.full_name or user.username}!', 'success')
                        
                        # Redirect to next page or dashboard
                        next_page = request.args.get('next')
                        return redirect(next_page) if next_page else redirect(url_for('homepage'))
                    else:
                        # Wrong password - increment failed attempts
                        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                        if user.failed_login_attempts >= 5:
                            user.lock_account(30)  # Lock for 30 minutes
                            flash('Too many failed login attempts. Account locked for 30 minutes.', 'error')
                        else:
                            flash(f'Invalid credentials. {5 - user.failed_login_attempts} attempts remaining.', 'error')
                        db.session.commit()
                        return render_template('auth/login.html')
                else:
                    # User not found
                    flash('Invalid credentials. Please check your username/email and password.', 'error')
                    return render_template('auth/login.html')
                    
            except Exception as db_error:
                print(f"⚠️ Database login check failed: {db_error}")
                flash('Login service temporarily unavailable. Please try again later.', 'error')
                return render_template('auth/login.html')
        
        # Demo login credentials (multiple formats for compatibility)
        demo_emails = [
            'admin@demo.com', 
            'demo@metabolomics.com', 
            'demo@metabolomics-platform.com',  # From backup
            'admin', 
            'demo'
        ]
        if username.lower() in [email.lower() for email in demo_emails] and password == 'admin123':
            session['user_authenticated'] = True
            session['user_email'] = username
            session['user_role'] = 'admin'
            flash('Demo login successful!', 'success')
            return redirect(url_for('homepage'))
        else:
            flash('Invalid credentials. Try demo: admin@demo.com / admin123 or check if your account exists.', 'error')
    
    # GET request - show login form
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Logout and clear session"""
    # Use Flask-Login logout if user is logged in
    if current_user.is_authenticated:
        logout_user()
    
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('homepage'))

@auth_bp.route('/oauth-login')
def oauth_login():
    """Initiate OAuth login with Google"""
    if not google:
        flash('OAuth service is not available.', 'error')
        return redirect(url_for('auth.login'))
    
    redirect_uri = url_for('auth.oauth_authorized', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route('/authorized')
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
        
        email = user_info.get('email')
        full_name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        
        # Check if user exists in database
        if db and User:
            user = User.query.filter_by(email=email).first()
            
            if user:
                # Existing user - update their info and login
                user.full_name = full_name or user.full_name
                user.picture = picture or user.picture
                user.last_login = datetime.utcnow()
                
                # If this is a local user switching to OAuth, update auth method
                if user.auth_method == 'password':
                    user.auth_method = 'dual'  # Now supports both
                elif user.auth_method != 'dual':
                    user.auth_method = 'oauth'
                
                db.session.commit()
                
            else:
                # New user - create account
                username = email.split('@')[0]  # Use email prefix as username
                counter = 1
                original_username = username
                
                # Ensure username is unique
                while User.query.filter_by(username=username).first():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    picture=picture,
                    auth_method='oauth',
                    is_active=True,
                    is_verified=True  # OAuth users are auto-verified
                )
                
                # Set admin role for loc22100302
                if username == 'loc22100302' or email == 'loc22100302@gmail.com':
                    user.role = 'admin'
                
                db.session.add(user)
                db.session.commit()
                
                flash(f'Welcome to the Metabolomics Platform, {full_name}!', 'success')
            
            # Login the user
            login_user(user, remember=True)
            
            # Set session variables for backward compatibility
            session['user_authenticated'] = True
            session['user_email'] = user.email
            session['user_role'] = user.role or 'user'
            session['user_auth_method'] = 'oauth'
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('homepage'))
        
        else:
            # Database not available - fallback session login
            session['user_authenticated'] = True
            session['user_email'] = email
            session['user_role'] = 'admin' if 'loc22100302' in email else 'user'
            session['user_auth_method'] = 'oauth'
            flash(f'Welcome, {full_name}!', 'success')
            return redirect(url_for('homepage'))
            
    except Exception as e:
        print(f"OAuth error: {e}")
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/register')
def register():
    """Registration page - redirect to local registration"""
    return redirect(url_for('auth.register_local'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password functionality with OAuth user handling"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password_new.html')
        
        # Check if user exists and handle OAuth users
        if db and User:
            user = User.query.filter_by(email=email).first()
            if user:
                # Check if this is an OAuth user
                auth_method = getattr(user, 'auth_method', 'local')
                
                if auth_method == 'oauth':
                    # OAuth users should use their provider's password reset
                    flash(f'This account uses Google OAuth authentication. To change your password, please visit your Google Account settings at https://myaccount.google.com/security', 'info')
                    return render_template('auth/forgot_password_oauth.html', 
                                        email=email, 
                                        provider='Google')
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
    
    return render_template('auth/forgot_password_new.html')

@auth_bp.route('/reset-password/<token>')
def reset_password_confirm(token):
    """Password reset confirmation page"""
    return render_template('auth/reset_password.html', token=token)

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
            if session.get(expiry_key, 0) < time.time():
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
            
            def is_admin(self):
                return self.role.lower() == 'admin'
        
        current_user = UserData(user_email, user_role, user_name, auth_method)
        
        return render_template('auth/profile.html', current_user=current_user, user=current_user)
    except Exception as e:
        print(f"⚠️ Profile route error: {e}")
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
                        self.password_updated_at = getattr(db_user, 'password_updated_at', None)
                except Exception as e:
                    print(f"⚠️ Error checking user password: {e}")
        
        def is_admin(self):
            return self.role.lower() == 'admin'
    
    current_user = EnhancedUser(user_email, user_role, user_name, auth_method)
    return render_template('auth/profile_password.html', current_user=current_user)

@auth_bp.route('/update-password', methods=['POST'])
def update_password():
    """Update user password"""
    if not session.get('user_authenticated', False):
        flash('Please log in to update your password.', 'error')
        return redirect(url_for('auth.login'))
    
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    user_email = session.get('user_email', '')
    
    # Validation
    if not new_password or not confirm_password:
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('auth.password_settings'))
    
    if new_password != confirm_password:
        flash('New password and confirmation do not match.', 'error')
        return redirect(url_for('auth.password_settings'))
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return redirect(url_for('auth.password_settings'))
    
    # Update password in database
    if db and User:
        try:
            user = User.query.filter_by(email=user_email).first()
            if user:
                # Check current password if user already has one
                if user.password_hash and current_password:
                    # Simple password check for demo - in production use proper hashing
                    if user.password_hash != current_password:
                        flash('Current password is incorrect.', 'error')
                        return redirect(url_for('auth.password_settings'))
                
                # Update password
                user.password_hash = new_password  # In production, use proper hashing
                from datetime import datetime
                user.password_updated_at = datetime.utcnow()
                
                db.session.commit()
                flash('Password updated successfully!', 'success')
            else:
                flash('User not found in database.', 'error')
        except Exception as e:
            print(f"⚠️ Password update error: {e}")
            flash('Error updating password. Please try again.', 'error')
    else:
        flash('Password update service not available.', 'error')
    
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
@login_required
def set_oauth_password():
    """Allow OAuth users to set a local password"""
    if not current_user.is_authenticated:
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
    
    try:
        # Set password for the user
        current_user.set_password(new_password)
        
        # Update auth method to support both OAuth and password
        if current_user.auth_method == 'oauth':
            current_user.auth_method = 'dual'  # Support both OAuth and password
        
        db.session.commit()
        
        action = 'updated' if current_user.password_hash else 'set'
        flash(f'Password {action} successfully! You can now login with either OAuth or your password.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while setting your password. Please try again.', 'error')
        print(f"Password setting error: {e}")
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/register-local', methods=['GET', 'POST'])
def register_local():
    """Local user registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        if not all([username, email, full_name, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register_local.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register_local.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/register_local.html')
        
        try:
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                flash('An account with this email already exists.', 'error')
                return render_template('auth/register_local.html')
            
            if User.query.filter_by(username=username).first():
                flash('This username is already taken.', 'error')
                return render_template('auth/register_local.html')
            
            # Create new user
            new_user = User(
                username=username,
                email=email,
                full_name=full_name,
                auth_method='password',
                is_active=True,
                is_verified=True  # Auto-verify for now, can add email verification later
            )
            new_user.set_password(password)
            
            # Set admin role for loc22100302
            if username == 'loc22100302':
                new_user.role = 'admin'
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating your account. Please try again.', 'error')
            print(f"Registration error: {e}")
    
    return render_template('auth/register_local.html')

@auth_bp.route('/manage-users')
@login_required
def manage_users():
    """User management interface for admins"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('auth/manage_users.html', users=users)

@auth_bp.route('/update-user-role', methods=['POST'])
@login_required
def update_user_role():
    """Update user role (admin only)"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    user_id = request.form.get('user_id')
    new_role = request.form.get('role')
    
    if not user_id or not new_role:
        flash('User ID and role are required.', 'error')
        return redirect(url_for('auth.manage_users'))
    
    if new_role not in ['user', 'manager', 'admin']:
        flash('Invalid role specified.', 'error')
        return redirect(url_for('auth.manage_users'))
    
    try:
        user = User.query.get(user_id)
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('auth.manage_users'))
        
        # Prevent admin from removing their own admin role
        if user.id == current_user.id and new_role != 'admin':
            flash('You cannot remove your own admin privileges.', 'error')
            return redirect(url_for('auth.manage_users'))
        
        old_role = user.role
        user.role = new_role
        db.session.commit()
        
        flash(f'User {user.username} role updated from {old_role} to {new_role}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating user role.', 'error')
        print(f"Role update error: {e}")
    
    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/change-password')
def change_password():
    """Redirect to new password settings page"""
    return redirect(url_for('auth.password_settings'))

# Register authentication blueprint
app.register_blueprint(auth_bp)
print("✅ Working authentication blueprint registered")

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

# === CONTEXT PROCESSOR FOR TEMPLATES ===
@app.context_processor
def inject_user():
    """Make current user info available to templates"""
    user_authenticated = session.get('user_authenticated', False)
    user_email = session.get('user_email', '')
    user_role = session.get('user_role', 'user')
    
    # Create a mock current_user for templates
    class MockUser:
        def __init__(self):
            self.is_authenticated = user_authenticated
            self.email = user_email
            self.full_name = user_email.split('@')[0] if user_email else 'Guest'
            self.role = user_role
        
        def is_admin(self):
            return self.role == 'admin'
        
        def is_manager(self):
            return self.role in ['admin', 'manager']
    
    return dict(current_user=MockUser())

# Decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash('Admin access required.', 'error')
            return redirect(url_for('homepage'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_manager():
            flash('Manager or Admin access required.', 'error')
            return redirect(url_for('homepage'))
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# HEALTH CHECK (BULLETPROOF)
# =====================================================

@app.route('/health')
def health_check():
    """Enhanced health check for Railway deployment debugging"""
    try:
        response_data = {
            "status": "healthy",
            "message": "Metabolomics platform operational",
            "timestamp": datetime.now().isoformat(),
            "version": "3.1.0-oauth-fixed",
            "environment": {
                "host": request.host,
                "user_agent": request.headers.get('User-Agent', 'Unknown'),
                "database_url_set": bool(os.getenv('DATABASE_URL')),
                "google_client_id_set": bool(os.getenv('GOOGLE_CLIENT_ID')),
                "secret_key_set": bool(os.getenv('SECRET_KEY'))
            },
            "features": {
                "flask": True,
                "database": bool(db),
                "authentication": bool(login_manager),
                "oauth": bool(google),
                "email": bool(mail),
                "charts": bool(DualChartService),
                "models": bool(MainLipid)
            }
        }
        return jsonify(response_data), 200
    except Exception as e:
        # Ultimate fallback - plain text response
        return f'{{"status":"healthy","message":"Platform running","error":"{str(e)}"}}', 200

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
        return render_template('browse_lipids.html')
    except Exception as e:
        print(f"⚠️ Browse lipids error: {e}")
        return f"<h1>Browse System Loading...</h1><p>Error: {e}</p>"

@app.route('/schedule', methods=['GET', 'POST'])
@app.route('/schedule-form', methods=['GET', 'POST'])
def schedule_form():
    """Schedule consultation form"""
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
                return render_template('schedule_form.html', today=date.today().isoformat())
            
            # Basic email validation
            if '@' not in email or '.' not in email:
                flash('Please provide a valid email address.', 'error')
                return render_template('schedule_form.html', today=date.today().isoformat())
            
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
                return render_template('schedule_form.html', today=date.today().isoformat())
                
            return redirect(url_for('schedule_form'))
            
        except Exception as e:
            flash(f'Error submitting request: {e}', 'error')
    
    try:
        from datetime import date
        return render_template('schedule_form.html', today=date.today().isoformat())
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
        return render_template('backup_management.html')
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

@app.route('/demo-login')
def demo_login():
    """Demo login for deployment testing - bypasses OAuth"""
    try:
        session['user_authenticated'] = True
        session['user_email'] = 'demo@metabolomics.com'
        session['user_role'] = 'admin'
        flash('Demo login successful!', 'success')
        return redirect(url_for('homepage'))
    except Exception as e:
        flash(f'Demo login failed: {e}', 'error')
        return redirect(url_for('auth.login'))

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
    """Google OAuth login with Railway domain support"""
    if google and OAUTH_AVAILABLE:
        try:
            # Handle domain properly for OAuth redirect
            host = request.host
            
            # Force HTTPS and handle both domain variants
            if 'httpsphenikaa-lipidomics-analysis.xyz' in host:
                # Use the www version with HTTPS as canonical
                redirect_uri = "https://www.httpsphenikaa-lipidomics-analysis.xyz/callback"
            else:
                # Fallback to standard Flask url_for for other domains
                redirect_uri = url_for('login_authorized', _external=True).replace('/login/authorized', '/callback')
                # Ensure HTTPS for production
                if redirect_uri.startswith('http://') and 'localhost' not in redirect_uri:
                    redirect_uri = redirect_uri.replace('http://', 'https://')
            
            print(f"🔗 OAuth redirect URI: {redirect_uri}")
            return google.authorize_redirect(redirect_uri)
        except Exception as e:
            print(f"⚠️ Google OAuth error: {e}")
            flash('Google OAuth error. Please try again or use demo login.', 'warning')
            return redirect(url_for('auth.login'))
    else:
        flash('Google OAuth not configured. Use demo login: admin@demo.com / admin123', 'warning')
        return redirect(url_for('auth.login'))

@app.route('/callback')
@app.route('/login/authorized')
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
            # Check if any admin users exist
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count == 0:
                # No admins exist, promote current user
                user_email = session.get('user_email')
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
# APPLICATION STARTUP
# =====================================================

print("🎯 ORIGINAL INTERFACE METABOLOMICS PLATFORM READY")
print("   All original features, navigation, and styling preserved")
print("   SQLAlchemy initialization fixed for bulletproof deployment")

@app.route('/ping')
def ping():
    """Simple ping endpoint for Railway health checks"""
    return "pong", 200

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

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors gracefully"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors gracefully"""
    return "Internal server error. Please try again later.", 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Starting Flask app on port {port}")
    print(f"🌐 Available at: http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    port = int(os.getenv('PORT', 8080))
    print(f"🚀 Gunicorn deployment on port {port}")
    print(f"🌐 Health check: /health, /ping, /status")

# For gunicorn
application = app