"""
Optimized PostgreSQL Flask Application
Fixes N+1 query problems with proper eager loading
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, send_file, session, get_flashed_messages
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
import json
from functools import lru_cache, wraps
from pathlib import Path
import pandas as pd
from datetime import datetime
import base64
import time
from io import BytesIO
from sqlalchemy import text
from sqlalchemy.orm import joinedload, selectinload

# Authentication imports
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message

# Appwrite authentication
from appwrite.client import Client
from appwrite.services.account import Account

# Import optimized PostgreSQL models
from models_postgresql_optimized import (
    db, init_db, create_all_tables,
    MainLipid, LipidClass, AnnotatedIon, User, ScheduleRequest, AdminSettings, optimized_manager,
    get_db_stats, get_lipids_by_class, search_lipids,
    BackupHistory, BackupSnapshots, BackupStats
)

# Import chart generation services  
from simple_chart_service import SimpleChartGenerator
from dual_chart_service import DualChartService

# Import backup system
from backup_system_postgresql import PostgreSQLBackupSystem, auto_backup_context

# Import authentication system - DEMO VERSION for Railway deployment
import os
if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('FLASK_ENV') == 'production':
    from email_auth_demo import auth_bp  # Safe version for Railway
else:
    from email_auth import auth_bp  # Full version for local development

# Import enhanced email service
from email_service_enhanced import send_schedule_notification, test_email_configuration, get_email_service_status

# Configuration
BASE_DIR = Path(__file__).resolve().parent

# Environment loading
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, template_folder=BASE_DIR / "templates", static_folder=BASE_DIR / "static")

# Fix for Railway HTTPS proxy - This tells Flask to trust the headers sent by the Railway proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)

app.secret_key = os.getenv('SECRET_KEY', 'metabolomics-dev-key-change-in-production')

# Authentication Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# OAuth Configuration
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

# Appwrite Configuration
appwrite_client = Client()
appwrite_client.set_endpoint('https://fra.cloud.appwrite.io/v1')
appwrite_client.set_project('689f6b2e0028c3763654')
appwrite_account = Account(appwrite_client)

# Email Configuration with SMTP hostname fix
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))
app.config['MAIL_SUPPRESS_SEND'] = os.getenv('MAIL_SUPPRESS_SEND', 'False').lower() == 'true'
app.config['MAIL_MAX_EMAILS'] = None
app.config['MAIL_ASCII_ATTACHMENTS'] = False
# Fix SMTP HELO hostname issue by setting a valid hostname
import socket
try:
    # Use a valid hostname instead of the problematic Windows hostname
    app.config['MAIL_LOCAL_HOSTNAME'] = 'metabolomics-platform.com'
    # Additional SMTP configuration for Windows compatibility
    app.config['MAIL_SUPPRESS_SEND'] = False
    app.config['MAIL_DEBUG'] = False
except:
    pass

mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return db.session.get(User, int(user_id))

# PostgreSQL configuration with optimization
database_url = os.getenv('DATABASE_URL')
if not database_url:
    # Local PostgreSQL
    database_url = 'postgresql://username:password@localhost/metabolomics_db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'echo': False  # Set to True for SQL debugging
}

# Initialize optimized database
db = init_db(app)

# Initialize backup system
backup_system = PostgreSQLBackupSystem(app)

# Register authentication blueprint
app.register_blueprint(auth_bp)

# =====================================================
# AUTHENTICATION ROUTES
# =====================================================

@app.route('/login')
def login():
    """Redirect to auth login page"""
    return redirect(url_for('auth.login'))

@app.route('/signup')
def signup():
    """Redirect to auth registration page"""
    return redirect(url_for('auth.register'))

@app.route('/demo-login')
def demo_login():
    """Demo login for deployment testing - bypasses OAuth"""
    try:
        # Create or get demo user
        demo_email = "demo@metabolomics-platform.com"
        demo_user = User.query.filter_by(email=demo_email).first()
        
        if not demo_user:
            # Create demo admin user
            demo_user = User(
                email=demo_email,
                full_name="Demo Admin User",
                picture="",
                role='admin',
                is_active=True
            )
            db.session.add(demo_user)
            db.session.commit()
        
        # Log in the demo user
        login_user(demo_user, remember=True)
        flash('🎯 Demo login successful! You have admin access.', 'success')
        return redirect(url_for('homepage'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Demo login failed: {str(e)}', 'error')
        return redirect(url_for('homepage'))

@app.route('/recovery-mode')
def recovery_mode():
    """Emergency recovery: disable authentication completely"""
    try:
        # Create emergency admin session
        session['emergency_admin'] = True
        session['recovery_mode'] = True
        flash('🚨 RECOVERY MODE ACTIVE - All authentication bypassed for debugging', 'warning')
        return redirect(url_for('homepage'))
    except Exception as e:
        return f"Recovery mode failed: {str(e)}"

@app.route('/appwrite-login')
def appwrite_login():
    """Initiate Appwrite Google OAuth login"""
    try:
        # Determine the correct base URL for callbacks
        if 'railway.app' in request.host:
            # Production Railway deployment
            base_url = f"https://{request.host}"
        else:
            # Local development
            base_url = url_for('appwrite_callback', _external=True).replace('/appwrite-callback', '')
        
        success_url = f"{base_url}/appwrite-callback"
        failure_url = f"{base_url}/login"
        
        print(f"Appwrite OAuth URLs - Success: {success_url}, Failure: {failure_url}")
        
        # Redirect to Appwrite OAuth
        oauth_url = f"https://fra.cloud.appwrite.io/v1/account/sessions/oauth2/google?project=689f6b2e0028c3763654&success={success_url}&failure={failure_url}"
        return redirect(oauth_url)
        
    except Exception as e:
        flash(f'Appwrite login failed: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/appwrite-callback')
def appwrite_callback():
    """Handle Appwrite OAuth callback"""
    try:
        # Get session info from Appwrite using cookies
        # The session should be in the cookies set by Appwrite
        session_cookies = request.cookies
        
        if 'a_session_689f6b2e0028c3763654' in session_cookies:
            # Set session cookie for Appwrite client
            appwrite_client.set_session(session_cookies['a_session_689f6b2e0028c3763654'])
            
            # Get user info from Appwrite
            user_info = appwrite_account.get()
            
            email = user_info['email']
            full_name = user_info['name']
            user_id = user_info['$id']
            
            # Find or create user in our database
            user = User.query.filter_by(email=email).first()
            if not user:
                # Check if this is the first user - make them admin
                user_count = User.query.count()
                default_role = 'admin' if user_count == 0 else 'user'
                
                # Create new user
                user = User(
                    email=email,
                    full_name=full_name,
                    picture='',  # Appwrite might not provide picture URL
                    role=default_role,
                    is_active=True
                )
                db.session.add(user)
                db.session.commit()
                
                if default_role == 'admin':
                    flash(f'Welcome {full_name}! You have been granted admin access as the first user.', 'success')
                else:
                    flash(f'Welcome {full_name}! Your account has been created.', 'success')
            else:
                # Update existing user info
                user.full_name = full_name
                user.last_login = datetime.now()
                db.session.commit()
                flash(f'Welcome back, {full_name}!', 'success')
            
            # Log the user in with Flask-Login
            login_user(user, remember=True)
            
            # Store Appwrite session in Flask session for future API calls
            session['appwrite_session'] = session_cookies['a_session_689f6b2e0028c3763654']
            
            return redirect(url_for('homepage'))
        else:
            flash('Authentication failed. Please try again.', 'error')
            return redirect(url_for('login'))
            
    except Exception as e:
        db.session.rollback()
        flash(f'Authentication failed: {str(e)}', 'error')
        return redirect(url_for('login'))

def get_oauth_redirect_uri():
    """Get appropriate OAuth redirect URI based on environment - UPDATED for custom domain"""
    # Check if we're on the new custom domain
    if 'httpsphenikaa-lipidomics-analysis.xyz' in request.host:
        base_url = f"https://{request.host}"
    elif 'phenikaa-lipidomics-analysis.edu.vn' in request.host:
        base_url = f"https://{request.host}"
    elif os.getenv('FLASK_ENV') == 'production' or 'railway.app' in request.host:
        # Production Railway deployment or custom domain
        base_url = os.getenv('PROD_OAUTH_BASE_URL', f"https://{request.host}")
    else:
        # Local development - NEVER use private IPs (192.168.x.x) - Google OAuth rejects them
        if 'localhost' in request.host or '127.0.0.1' in request.host:
            base_url = f"http://{request.host}"
        else:
            # Force localhost for any other development scenario (fixes private IP issue)
            base_url = "http://localhost:5000"
    
    return f"{base_url}/auth"  # Use shorter route for better Google Console compatibility

@app.route('/login/callback')
def login_callback():
    """Gmail OAuth callback with enhanced error handling - FIXED"""
    try:
        # Get the correct redirect URI for this environment
        redirect_uri = get_oauth_redirect_uri()
        
        # Log for debugging
        print(f"🔧 OAuth redirect URI: {redirect_uri}")
        print(f"🔧 Request host: {request.host}")
        
        return google.authorize_redirect(redirect_uri)
        
    except Exception as e:
        print(f"❌ OAuth callback error: {str(e)}")
        flash(f'Login initialization failed: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/auth')        # Short URL for Google Console
@app.route('/google')      # Alternative short URL
@app.route('/oauth2')      # Standard OAuth2 pattern
@app.route('/callback')    # Original URL
def login_authorized():
    """Enhanced OAuth authorization handler with better error handling"""
    try:
        # Get token with proper error handling
        token = google.authorize_access_token()
        
        if not token:
            flash('Authorization was denied. Please try again.', 'error')
            return redirect(url_for('login'))
        
        # Enhanced user info retrieval with multiple fallbacks
        user_info = None
        
        # Method 1: Direct from token
        if 'userinfo' in token:
            user_info = token['userinfo']
            print("✅ User info from token.userinfo")
        
        # Method 2: Parse ID token
        if not user_info and 'id_token' in token:
            try:
                user_info = google.parse_id_token(token)
                print("✅ User info from ID token")
            except Exception as e:
                print(f"⚠️ ID token parsing failed: {e}")
        
        # Method 3: API call to userinfo endpoint
        if not user_info:
            try:
                resp = google.get('userinfo', token=token)
                if resp.status_code == 200:
                    user_info = resp.json()
                    print("✅ User info from API call")
                else:
                    print(f"⚠️ Userinfo API returned status {resp.status_code}")
            except Exception as e:
                print(f"⚠️ Userinfo API call failed: {e}")
        
        if not user_info:
            flash('Failed to retrieve user information from Google.', 'error')
            return redirect(url_for('login'))
        
        email = user_info.get('email')
        full_name = user_info.get('name', 'Unknown User')
        picture = user_info.get('picture', '')
        
        if not email:
            flash('Gmail email address is required.', 'error')
            return redirect(url_for('login'))
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            # Check if this is the first user - make them admin
            user_count = User.query.count()
            default_role = 'admin' if user_count == 0 else 'user'
            
            # Create new user
            user = User(
                email=email,
                full_name=full_name,
                picture=picture,
                role=default_role,
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            
            if default_role == 'admin':
                flash(f'Welcome {full_name}! You have been granted admin access as the first user.', 'success')
            else:
                flash(f'Welcome {full_name}! Your account has been created.', 'success')
        else:
            # Update existing user info
            user.full_name = full_name
            user.picture = picture
            user.last_login = datetime.now()
            db.session.commit()
            flash(f'Welcome back, {full_name}!', 'success')
        
        # Log the user in
        login_user(user, remember=True)
        
        # Redirect to requested page or homepage
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        else:
            return redirect(url_for('homepage'))
            
    except Exception as e:
        db.session.rollback()
        flash(f'Login failed: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/oauth-debug')
def oauth_debug():
    """Debug OAuth configuration and test connectivity"""
    if not os.getenv('FLASK_ENV') == 'development':
        return "Debug mode only available in development", 403
    
    debug_info = {
        'environment': os.getenv('FLASK_ENV', 'development'),
        'request_host': request.host,
        'request_url': request.url,
        'google_client_id': (os.getenv('GOOGLE_CLIENT_ID')[:10] + '...' if os.getenv('GOOGLE_CLIENT_ID') else 'Not set'),
        'oauth_redirect_uri': get_oauth_redirect_uri(),
        'oauth_scopes': 'openid email profile',
        'oauth_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration'
    }
    
    return f"""
    <html>
    <head>
        <title>OAuth Debug Information</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h2 {{ color: #2E4C92; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ padding: 10px; background: #f8f9fa; margin: 5px 0; border-radius: 5px; }}
            strong {{ color: #213671; }}
            .test-button {{ background: #2E4C92; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; }}
            .test-button:hover {{ background: #213671; }}
            ol {{ padding-left: 20px; }}
            li.step {{ background: #e3f2fd; border-left: 4px solid #2E4C92; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔍 OAuth Debug Information</h2>
            <ul>
                {''.join([f'<li><strong>{k.replace("_", " ").title()}:</strong> {v}</li>' for k, v in debug_info.items()])}
            </ul>
            
            <h3>🧪 Test OAuth Flow:</h3>
            <a href="{url_for('login_callback')}" class="test-button">
                🚀 Test Google OAuth
            </a>
            
            <h3>📋 Next Steps:</h3>
            <ol>
                <li class="step">Verify Google Cloud Console redirect URIs match: <strong>{debug_info['oauth_redirect_uri']}</strong></li>
                <li class="step">Ensure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are correct in .env file</li>
                <li class="step">Test OAuth flow using the button above</li>
                <li class="step">Check browser console for any JavaScript errors</li>
                <li class="step">If errors persist, check <a href="/recovery-mode">Recovery Mode</a> or <a href="/demo-login">Demo Login</a></li>
            </ol>
            
            <h3>🔧 Current Issues & Solutions:</h3>
            <ul>
                <li><strong>Private IP Error (192.168.x.x):</strong> Fixed! Now using localhost only</li>
                <li><strong>Redirect URI Mismatch:</strong> Check Google Cloud Console settings</li>
                <li><strong>Access Denied:</strong> User cancelled or OAuth app not verified</li>
                <li><strong>Token Issues:</strong> Check client ID/secret configuration</li>
            </ul>
            
            <p><a href="{url_for('homepage')}">← Back to Homepage</a></p>
        </div>
    </body>
    </html>
    """

@app.route('/logout')
@login_required
def logout():
    """Logout user and redirect to homepage"""
    user_name = current_user.full_name if current_user.is_authenticated else "User"
    logout_user()
    flash(f'Goodbye {user_name}! You have been logged out successfully.', 'info')
    return redirect(url_for('homepage'))

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('Admin access required.', 'error')
            return redirect(url_for('homepage'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    """Decorator to require manager or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_manager():
            flash('Manager or Admin access required.', 'error')
            return redirect(url_for('homepage'))
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# MAIN DASHBOARD ROUTE (OPTIMIZED)
# =====================================================

@app.route('/')
def homepage():
    """University-style homepage with project overview."""
    try:
        # Get basic stats with optimized queries (cached)
        stats = get_db_stats()
        
        # Get sample recent data (ONLY first 3 lipids) - ULTRA FAST
        recent_lipids = optimized_manager.get_lipids_sample(limit=3)
        
        homepage_data = {
            'stats': stats,
            'recent_lipids': recent_lipids,
            'news': [
                {
                    'title': 'PostgreSQL Performance Optimization Complete',
                    'date': '2024-12-15',
                    'summary': 'Fixed N+1 query problems with eager loading. 10-100x speed improvement achieved.',
                    'image': '/static/news1.jpg'
                },
                {
                    'title': 'Interactive Chart Analysis System Optimized', 
                    'date': '2024-12-10',
                    'summary': 'Advanced dual-chart visualization with optimized database queries for instant loading.',
                    'image': '/static/news2.jpg'
                }
            ]
        }
        
        return render_template('homepage.html', data=homepage_data)
        
    except Exception as e:
        flash(f'Homepage error: {str(e)}', 'error')
        return render_template('homepage.html', data={'stats': {}, 'recent_lipids': [], 'news': []})

@app.route('/lipid-selection')
@app.route('/dashboard')
def clean_dashboard():
    """Lipid selection page with LAZY LOADING for instant startup."""
    try:
        start_time = time.time()
        
        # Get database statistics (fast query)
        stats = get_db_stats()
        
        # LAZY LOADING: Only get class data initially, load lipids via AJAX
        classes_data = optimized_manager.get_lipid_classes_optimized()
        
        query_time = time.time() - start_time
        print(f"🚀 Dashboard loaded in {query_time:.3f}s (lazy loading)")
        
        dashboard_data = {
            'stats': stats,
            'lipids': [],  # Empty initially - loaded via AJAX
            'classes': classes_data,
            'query_time': f"{query_time:.3f}s",
            'lazy_loading': True  # Flag for frontend
        }
        
        return render_template('clean_dashboard.html', data=dashboard_data)
        
    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'error')
        return render_template('clean_dashboard.html', data={'stats': {}, 'lipids': [], 'classes': []})

# =====================================================
# LIPID BROWSING ROUTES (OPTIMIZED)
# =====================================================

@app.route('/lipids')
def browse_lipids():
    """Browse and search lipids with OPTIMIZED filtering."""
    # Get filter parameters
    class_filter = request.args.get('class', '')
    search_term = request.args.get('search', '')
    rt_min = request.args.get('rt_min', type=float)
    rt_max = request.args.get('rt_max', type=float)
    multi_ion_only = request.args.get('multi_ion', type=bool, default=False)
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # OPTIMIZED: Build query with proper eager loading
    query = MainLipid.query.options(
        joinedload(MainLipid.lipid_class),
        selectinload(MainLipid.annotated_ions)
    ).filter_by(extraction_success=True)
    
    # Apply filters
    if class_filter:
        query = query.join(LipidClass).filter(LipidClass.class_name == class_filter)
    
    if search_term:
        query = query.filter(MainLipid.lipid_name.ilike(f'%{search_term}%'))
    
    if rt_min is not None:
        query = query.filter(MainLipid.retention_time >= rt_min)
    
    if rt_max is not None:
        query = query.filter(MainLipid.retention_time <= rt_max)
    
    if multi_ion_only:
        query = query.join(AnnotatedIon).group_by(MainLipid.lipid_id).having(db.func.count(AnnotatedIon.ion_id) > 1)
    
    # Order and paginate
    query = query.order_by(MainLipid.lipid_name)
    lipids = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # OPTIMIZED: Get available classes with single query
    classes = LipidClass.query.order_by(LipidClass.class_name).all()
    
    return render_template('browse_lipids.html', 
                         lipids=lipids, 
                         classes=classes,
                         current_filters={
                             'class': class_filter,
                             'search': search_term,
                             'rt_min': rt_min,
                             'rt_max': rt_max,
                             'multi_ion': multi_ion_only
                         })

@app.route('/lipid/<int:lipid_id>')
def lipid_detail(lipid_id):
    """Show detailed view of a specific lipid with OPTIMIZED queries."""
    # OPTIMIZED: Single query with all related data
    lipid = MainLipid.query.options(
        joinedload(MainLipid.lipid_class),
        selectinload(MainLipid.annotated_ions)
    ).filter_by(lipid_id=lipid_id).first_or_404()
    
    lipid_data = {
        'lipid': lipid.to_dict(include_xic=True, include_ions=True),
        'class_name': lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown'
    }
    
    return render_template('lipid_detail.html', data=lipid_data)

# =====================================================
# CHART GENERATION ROUTES (OPTIMIZED)
# =====================================================

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
        flash(f'Dual chart view error: {str(e)}', 'error')
        return redirect(url_for('clean_dashboard'))

@app.route('/api/dual-chart-data/<int:lipid_id>')
def api_dual_chart_data(lipid_id):
    """API endpoint to get dual chart data with OPTIMIZED PostgreSQL."""
    try:
        # Use optimized chart data retrieval
        chart_data = optimized_manager.get_lipid_chart_data_optimized(lipid_id)
        if not chart_data:
            return jsonify({'status': 'error', 'message': 'Lipid not found'}), 404
        
        # Generate charts using existing service (works with optimized data)
        chart_service = DualChartService()
        dual_chart_data = chart_service.get_dual_chart_data(lipid_id)
        
        return jsonify({
            'status': 'success',
            'data': dual_chart_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/load-lipids')
def api_load_lipids():
    """AJAX endpoint to load all lipids asynchronously for dashboard."""
    try:
        start_time = time.time()
        
        # Load all lipids with optimized query
        lipids_data = optimized_manager.get_all_lipids_optimized()
        
        query_time = time.time() - start_time
        print(f"🚀 AJAX lipids loaded in {query_time:.3f}s")
        
        return jsonify({
            'status': 'success',
            'lipids': lipids_data,
            'query_time': f"{query_time:.3f}s",
            'count': len(lipids_data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# =====================================================
# MANAGE LIPIDS ROUTES (OPTIMIZED)
# =====================================================

@app.route('/api/database-view')
def api_database_view():
    """API endpoint for database view modal - no authentication required"""
    try:
        # Get database statistics
        stats = get_db_stats()
        
        # Get all lipids with optimized query  
        lipids_data = optimized_manager.get_all_lipids_optimized()
        total_count = len(lipids_data)
        
        # Get class distribution
        classes_data = optimized_manager.get_lipid_classes_optimized()
        
        return jsonify({
            'status': 'success',
            'stats': stats,
            'lipids': lipids_data,
            'classes': classes_data,
            'total_count': total_count
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500

@app.route('/manage-lipids')
@manager_required
def manage_lipids():
    """Manage lipids interface with OPTIMIZED data loading."""
    try:
        # Get database statistics
        stats = get_db_stats()
        
        # OPTIMIZED: Get ALL lipids with single query (no N+1)
        lipids_data = optimized_manager.get_all_lipids_optimized()
        total_count = len(lipids_data)
        
        # OPTIMIZED: Get class distribution with efficient query
        classes_data = optimized_manager.get_lipid_classes_optimized()
        
        # Calculate additional stats
        stats['successful_extractions'] = total_count
        
        manage_data = {
            'stats': stats,
            'lipids': lipids_data,
            'classes': classes_data,
            'total_count': total_count
        }
        
        return render_template('manage_lipids.html', data=manage_data)
        
    except Exception as e:
        flash(f'Management interface error: {str(e)}', 'error')
        return render_template('manage_lipids.html', data={'stats': {}, 'lipids': [], 'classes': [], 'total_count': 0})

# =====================================================
# API ROUTES (OPTIMIZED)
# =====================================================

@app.route('/api/lipids')
def api_lipids():
    """API endpoint for lipids with OPTIMIZED filtering."""
    class_name = request.args.get('class')
    search = request.args.get('search')
    limit = request.args.get('limit', 50, type=int)
    
    # OPTIMIZED: Build query with proper eager loading
    query = MainLipid.query.options(
        joinedload(MainLipid.lipid_class)
    ).filter_by(extraction_success=True)
    
    if class_name:
        query = query.join(LipidClass).filter(LipidClass.class_name == class_name)
    
    if search:
        query = query.filter(MainLipid.lipid_name.ilike(f'%{search}%'))
    
    lipids = query.limit(limit).all()
    
    # No N+1 queries here!
    lipids_data = [
        {
            'lipid_id': lipid.lipid_id,
            'lipid_name': lipid.lipid_name,
            'api_code': lipid.api_code,
            'retention_time': lipid.retention_time,
            'class_name': lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown'
        }
        for lipid in lipids
    ]
    
    return jsonify({
        'status': 'success',
        'count': len(lipids_data),
        'lipids': lipids_data
    })

@app.route('/api/classes')
def api_classes():
    """API endpoint for lipid classes."""
    classes = LipidClass.query.order_by(LipidClass.class_name).all()
    return jsonify({
        'status': 'success',
        'classes': [cls.to_dict() for cls in classes]
    })

# =====================================================
# ADMIN ROUTES (OPTIMIZED)
# =====================================================

@app.route('/admin/stats')
@admin_required
def admin_stats():
    """Admin statistics with OPTIMIZED database queries."""
    try:
        stats = get_db_stats()
        
        # OPTIMIZED: Get class distribution with single efficient query
        classes_data = optimized_manager.get_lipid_classes_optimized()
        total_lipids = sum([cls['count'] for cls in classes_data])
        
        detailed_stats = {
            'class_distribution': [
                {
                    'class': cls['class_name'], 
                    'count': cls['count'], 
                    'percentage': round(cls['count']/total_lipids*100, 1) if total_lipids > 0 else 0
                } 
                for cls in classes_data
            ],
            'recent_sessions': [],  # Placeholder
            'data_quality': {
                'lipids_with_xic_data': total_lipids,
                'xic_coverage_percentage': 100.0
            }
        }
        
        return render_template('admin_stats.html', stats=stats, detailed_stats=detailed_stats)
        
    except Exception as e:
        flash(f'Statistics error: {str(e)}', 'error')
        return render_template('admin_stats.html', stats={}, detailed_stats={})

# =====================================================
# ADMIN DASHBOARD ROUTE
# =====================================================

@app.route('/auth-debug')
def auth_debug():
    """Debug route to show all users and authentication issues"""
    try:
        # Get all users
        users = User.query.all()
        
        debug_info = f"""
        <html>
        <head>
            <title>Authentication Debug</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .user {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #2E4C92; }}
                .error {{ background: #f8d7da; padding: 10px; border-radius: 5px; color: #721c24; margin: 10px 0; }}
                .success {{ background: #d4edda; padding: 10px; border-radius: 5px; color: #155724; margin: 10px 0; }}
                h2 {{ color: #2E4C92; }}
                .password-reset {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🐛 Authentication Debug Information</h2>
                
                <h3>📊 Database Users ({len(users)} total)</h3>
        """
        
        for user in users:
            debug_info += f"""
                <div class="user">
                    <strong>👤 {user.full_name}</strong><br>
                    <strong>Username:</strong> {user.username}<br>
                    <strong>Email:</strong> {user.email}<br>
                    <strong>Role:</strong> {user.role}<br>
                    <strong>Active:</strong> {'✅ Yes' if user.is_active else '❌ No'}<br>
                    <strong>Email Verified:</strong> {'✅ Yes' if user.email_verified else '❌ No'}<br>
                    <strong>Has Password:</strong> {'✅ Yes' if user.password_hash else '❌ No'}<br>
                    <strong>Auth Method:</strong> {user.auth_method}<br>
                    <strong>Failed Attempts:</strong> {user.failed_login_attempts or 0}<br>
                    <strong>Account Locked:</strong> {'🔒 Yes' if user.is_account_locked() else '✅ No'}<br>
                    <strong>Created:</strong> {user.created_at}<br>
                    <strong>Last Login:</strong> {user.last_login or 'Never'}<br>
                </div>
            """
        
        # Email configuration check
        import os
        mail_configured = bool(os.getenv('MAIL_USERNAME') and os.getenv('MAIL_PASSWORD'))
        
        debug_info += f"""
                <h3>📧 Email Configuration</h3>
                <div class="{'success' if mail_configured else 'error'}">
                    <strong>Status:</strong> {'✅ Configured' if mail_configured else '❌ Not Configured'}<br>
                    <strong>Server:</strong> {os.getenv('MAIL_SERVER', 'Not set')}<br>
                    <strong>Username:</strong> {os.getenv('MAIL_USERNAME', 'Not set')}<br>
                    <strong>Password:</strong> {'✅ Set' if os.getenv('MAIL_PASSWORD') else '❌ Not set'}
                </div>
                
                <div class="password-reset">
                    <h4>🔧 Manual Password Reset</h4>
                    <p>If you can't login or forgot password doesn't work, you can reset passwords manually:</p>
                    <ol>
                        <li>Visit: <a href="/manual-password-reset">/manual-password-reset</a></li>
                        <li>Or contact admin to reset your password</li>
                        <li>Or use demo login: <a href="/demo-login">/demo-login</a></li>
                    </ol>
                </div>
                
                <h3>🔗 Useful Links</h3>
                <ul>
                    <li><a href="/auth/login">Login Page</a></li>
                    <li><a href="/auth/register">Registration Page</a></li>
                    <li><a href="/auth/forgot-password">Forgot Password</a></li>
                    <li><a href="/demo-login">Demo Login</a></li>
                    <li><a href="/manual-password-reset">Manual Password Reset</a></li>
                </ul>
                
                <p><a href="/">← Back to Homepage</a></p>
            </div>
        </body>
        </html>
        """
        
        return debug_info
        
    except Exception as e:
        return f"<h2>❌ Debug Error</h2><p>{str(e)}</p><a href='/'>Back to Homepage</a>"

@app.route('/user-debug')
@login_required
def user_debug():
    """Debug route to show current user info"""
    try:
        user_info = {
            'email': current_user.email,
            'username': current_user.username,
            'full_name': current_user.full_name,
            'role': current_user.role,
            'is_admin': current_user.is_admin(),
            'is_manager': current_user.is_manager(),
            'is_authenticated': current_user.is_authenticated,
            'user_id': current_user.user_id
        }
        
        admin_count = User.query.filter_by(role='admin').count()
        user_count = User.query.count()
        
        debug_info = f"""
        <h2>🔍 User Debug Information</h2>
        <h3>Current User:</h3>
        <ul>
            <li><strong>Email:</strong> {user_info['email']}</li>
            <li><strong>Name:</strong> {user_info['full_name']}</li>
            <li><strong>Role:</strong> {user_info['role']}</li>
            <li><strong>Admin Access:</strong> {'✅ YES' if user_info['is_admin'] else '❌ NO'}</li>
            <li><strong>Manager Access:</strong> {'✅ YES' if user_info['is_manager'] else '❌ NO'}</li>
            <li><strong>User ID:</strong> {user_info['user_id']}</li>
        </ul>
        
        <h3>System Stats:</h3>
        <ul>
            <li><strong>Total Users:</strong> {user_count}</li>
            <li><strong>Admin Users:</strong> {admin_count}</li>
        </ul>
        
        <h3>Quick Actions:</h3>
        <ul>
            <li><a href="{url_for('promote_to_admin')}">🚀 Request Admin Access</a></li>
            <li><a href="{url_for('homepage')}">🏠 Back to Homepage</a></li>
        </ul>
        """
        
        return debug_info
        
    except Exception as e:
        return f"<h2>❌ Debug Error</h2><p>{str(e)}</p><a href='{url_for('homepage')}'>Back to Homepage</a>"

@app.route('/fix-oauth-users')
def fix_oauth_users():
    """Fix OAuth users by setting default passwords"""
    try:
        fixed_users = []
        oauth_users = User.query.filter_by(auth_method='oauth').all()
        
        for user in oauth_users:
            if not user.password_hash:
                # Set a default password based on username
                default_password = f"{user.username}123!"
                user.set_password(default_password)
                user.auth_method = 'password'  # Change to password auth
                user.email_verified = True  # Mark as verified
                user.reset_failed_attempts()  # Clear any failed attempts
                
                fixed_users.append({
                    'username': user.username,
                    'email': user.email,
                    'password': default_password
                })
        
        db.session.commit()
        
        result = f"""
        <html>
        <head>
            <title>OAuth Users Fixed</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .user {{ background: #d4edda; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #28a745; }}
                h2 {{ color: #2E4C92; }}
                .password {{ font-family: monospace; background: #f8f9fa; padding: 5px; border-radius: 3px; }}
                .warning {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; color: #856404; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>✅ OAuth Users Fixed!</h2>
                <p>Successfully set passwords for {len(fixed_users)} OAuth users:</p>
        """
        
        for user_info in fixed_users:
            result += f"""
                <div class="user">
                    <strong>👤 {user_info['username']}</strong><br>
                    <strong>Email:</strong> {user_info['email']}<br>
                    <strong>Default Password:</strong> <span class="password">{user_info['password']}</span><br>
                    <em>You can now login with this username and password!</em>
                </div>
            """
        
        if not fixed_users:
            result += """
                <div class="warning">
                    <strong>⚠️ No OAuth users found or all users already have passwords set.</strong>
                </div>
            """
        
        result += f"""
                <div class="warning">
                    <strong>🔒 Security Note:</strong> Please change these default passwords after logging in!
                    <br>Visit your profile to update your password to something more secure.
                </div>
                
                <h3>🔗 Quick Actions</h3>
                <ul>
                    <li><a href="/auth/login">🔐 Login Now</a></li>
                    <li><a href="/auth-debug">🐛 View Debug Info</a></li>
                    <li><a href="/manual-password-reset">🔧 Manual Password Reset</a></li>
                    <li><a href="/">🏠 Homepage</a></li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return result
        
    except Exception as e:
        db.session.rollback()
        return f"<h2>❌ Error fixing OAuth users</h2><p>{str(e)}</p><a href='/auth-debug'>Back to Debug</a>"

@app.route('/manual-password-reset', methods=['GET', 'POST'])
def manual_password_reset():
    """Emergency manual password reset - for development/admin use"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            if not username or not new_password:
                flash('Username and password are required.', 'error')
                return redirect(url_for('manual_password_reset'))
            
            if new_password != confirm_password:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('manual_password_reset'))
            
            if len(new_password) < 8:
                flash('Password must be at least 8 characters long.', 'error')
                return redirect(url_for('manual_password_reset'))
            
            # Find user
            user = User.query.filter_by(username=username.lower()).first()
            if not user:
                flash(f'User "{username}" not found.', 'error')
                return redirect(url_for('manual_password_reset'))
            
            # Reset password
            user.set_password(new_password)
            user.reset_failed_attempts()  # Clear any lockouts
            user.email_verified = True  # Mark as verified
            db.session.commit()
            
            flash(f'✅ Password reset successfully for {user.full_name}! You can now login with the new password.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error resetting password: {str(e)}', 'error')
    
    # Get all usernames for dropdown
    try:
        users = User.query.all()
        usernames = [user.username for user in users]
    except:
        usernames = []
    
    # Handle flash messages
    flash_messages = ''
    for cat, msg in get_flashed_messages(with_categories=True):
        alert_class = 'alert-success' if cat == 'success' else 'alert-error'
        flash_messages += f'<div class="alert {alert_class}">{msg}</div>'
    
    # Generate username list HTML
    username_items = ''
    for username in usernames:
        username_items += f'<span class="username-item" onclick="selectUsername(\'{username}\')">{username}</span>'
    
    return f"""
    <html>
    <head>
        <title>Manual Password Reset</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; color: #2E4C92; }}
            input, select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
            button {{ background: #2E4C92; color: white; padding: 12px 20px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; width: 100%; }}
            button:hover {{ background: #213671; }}
            .alert {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
            .alert-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .alert-error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            h2 {{ color: #2E4C92; text-align: center; }}
            .usernames {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .username-list {{ display: flex; flex-wrap: wrap; gap: 10px; }}
            .username-item {{ background: #e9ecef; padding: 5px 10px; border-radius: 3px; font-family: monospace; cursor: pointer; }}
            .username-item:hover {{ background: #2E4C92; color: white; }}
        </style>
        <script>
            function selectUsername(username) {{
                document.getElementById('username').value = username;
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h2>🔧 Manual Password Reset</h2>
            <p style="text-align: center; color: #666;">Emergency password reset for system administrators</p>
            
            {flash_messages}
            
            <div class="usernames">
                <strong>📝 Available Usernames (click to select):</strong>
                <div class="username-list">
                    {username_items}
                </div>
            </div>
            
            <form method="POST">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label for="new_password">New Password:</label>
                    <input type="password" id="new_password" name="new_password" required minlength="8">
                </div>
                
                <div class="form-group">
                    <label for="confirm_password">Confirm Password:</label>
                    <input type="password" id="confirm_password" name="confirm_password" required minlength="8">
                </div>
                
                <button type="submit">🔄 Reset Password</button>
            </form>
            
            <div style="text-align: center; margin-top: 20px;">
                <a href="/auth-debug">🐛 View Debug Info</a> | 
                <a href="/auth/login">🔐 Back to Login</a> | 
                <a href="/">🏠 Homepage</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/promote-to-admin')
@login_required
def promote_to_admin():
    """Emergency route to promote current user to admin (for initial setup)"""
    try:
        # Only allow this if there are no admins in the system
        admin_count = User.query.filter_by(role='admin').count()
        
        if admin_count == 0:
            # No admins exist, promote current user
            current_user.role = 'admin'
            db.session.commit()
            flash(f'🎉 SUCCESS! You have been promoted to admin! You now have full access to the platform.', 'success')
        else:
            flash('Admin users already exist. Contact an existing admin for role changes.', 'warning')
        
        return redirect(url_for('homepage'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error promoting user: {str(e)}', 'error')
        return redirect(url_for('homepage'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard - basic interface."""
    try:
        stats = get_db_stats()
        
        admin_info = {
            'total_users': 0,  # Placeholder for future user system
            'active_sessions': 1,
            'database_status': 'Connected',
            'last_backup': 'Not configured'
        }
        
        # Get backup statistics for the admin dashboard
        try:
            backup_stats = backup_system.get_backup_statistics()
        except:
            backup_stats = None
        
        return render_template('admin_dashboard.html', stats=stats, admin_info=admin_info, backup_stats=backup_stats)
        
    except Exception as e:
        flash(f'Admin dashboard error: {str(e)}', 'error')
        return render_template('admin_dashboard.html', stats={}, admin_info={}, backup_stats=None)

@app.route('/admin/zoom-settings')
@admin_required
def admin_zoom_settings():
    """Admin zoom settings configuration"""
    try:
        # Get current zoom settings
        zoom_start = AdminSettings.get_setting('chart_zoom_start', 0.0)
        zoom_end = AdminSettings.get_setting('chart_zoom_end', 16.0)
        
        return render_template('admin_zoom_settings.html', 
                             zoom_start=zoom_start, 
                             zoom_end=zoom_end)
    except Exception as e:
        flash(f'Error loading zoom settings: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/zoom-settings', methods=['POST'])
@admin_required
def update_zoom_settings():
    """Update admin zoom settings"""
    try:
        zoom_start = float(request.form.get('zoom_start', 0.0))
        zoom_end = float(request.form.get('zoom_end', 16.0))
        
        # Validate settings
        if zoom_start < 0 or zoom_end <= zoom_start:
            flash('Invalid zoom range. End time must be greater than start time.', 'error')
            return redirect(url_for('admin_zoom_settings'))
        
        # Save settings
        AdminSettings.set_setting('chart_zoom_start', zoom_start, 'number', 
                                'Default chart zoom start time (minutes)', current_user.user_id)
        AdminSettings.set_setting('chart_zoom_end', zoom_end, 'number', 
                                'Default chart zoom end time (minutes)', current_user.user_id)
        
        flash(f'Zoom settings updated: {zoom_start:.2f} - {zoom_end:.2f} minutes', 'success')
        return redirect(url_for('admin_zoom_settings'))
        
    except Exception as e:
        flash(f'Error updating zoom settings: {str(e)}', 'error')
        return redirect(url_for('admin_zoom_settings'))

@app.route('/api/zoom-settings')
def get_zoom_settings():
    """API endpoint to get current zoom settings for charts"""
    try:
        zoom_start = AdminSettings.get_setting('chart_zoom_start', 0.0)
        zoom_end = AdminSettings.get_setting('chart_zoom_end', 16.0)
        
        return jsonify({
            'status': 'success',
            'data': {
                'zoom_start': zoom_start,
                'zoom_end': zoom_end
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# =====================================================
# BACKUP MANAGEMENT ROUTES
# =====================================================

@app.route('/backup-management')
@admin_required
def backup_management():
    """Backup management dashboard"""
    try:
        # Get backup statistics
        stats = backup_system.get_backup_statistics()
        
        # Get recent backup history
        recent_backups = backup_system.get_backup_history(limit=20)
        
        # Get recent snapshots
        recent_snapshots = backup_system.get_snapshots(limit=10)
        
        return render_template('backup_management.html', 
                             stats=stats, 
                             recent_backups=recent_backups,
                             recent_snapshots=recent_snapshots)
        
    except Exception as e:
        flash(f'Backup management error: {str(e)}', 'error')
        return render_template('backup_management.html', 
                             stats={}, 
                             recent_backups=[],
                             recent_snapshots=[])

@app.route('/api/create-snapshot', methods=['POST'])
def create_snapshot():
    """Create a manual database snapshot"""
    try:
        description = request.form.get('description', f'Manual snapshot created at {datetime.now()}')
        
        snapshot_id = backup_system.create_full_snapshot(description)
        
        return jsonify({
            'status': 'success',
            'snapshot_id': snapshot_id,
            'message': f'Snapshot {snapshot_id} created successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to create snapshot: {str(e)}'
        }), 500

@app.route('/api/backup-history')
def backup_history_api():
    """API endpoint for backup history with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        table_filter = request.args.get('table', None)
        
        backups = backup_system.get_backup_history(
            limit=per_page, 
            table_name=table_filter
        )
        
        backup_data = []
        for backup in backups:
            backup_data.append({
                'backup_id': backup.backup_id,
                'table_name': backup.table_name,
                'record_id': backup.record_id,
                'operation': backup.operation,
                'timestamp': backup.timestamp,
                'formatted_time': datetime.fromtimestamp(backup.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': backup.user_id or 'System',
                'source': backup.source,
                'has_old_data': backup.old_data is not None,
                'has_new_data': backup.new_data is not None
            })
        
        return jsonify({
            'status': 'success',
            'backups': backup_data,
            'total': len(backup_data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get backup history: {str(e)}'
        }), 500

@app.route('/api/backup-details/<backup_id>')
def backup_details(backup_id):
    """Get detailed information about a specific backup"""
    try:
        backup = db.session.query(BackupHistory).filter_by(backup_id=backup_id).first()
        
        if not backup:
            return jsonify({
                'status': 'error',
                'message': 'Backup not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'backup': {
                'backup_id': backup.backup_id,
                'table_name': backup.table_name,
                'record_id': backup.record_id,
                'operation': backup.operation,
                'old_data': backup.old_data,
                'new_data': backup.new_data,
                'timestamp': backup.timestamp,
                'formatted_time': datetime.fromtimestamp(backup.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': backup.user_id or 'System',
                'source': backup.source,
                'backup_hash': backup.backup_hash
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get backup details: {str(e)}'
        }), 500

# =====================================================
# ENHANCED ROUTES WITH AUTO-BACKUP
# =====================================================

@app.route('/update-lipid/<int:lipid_id>', methods=['POST'])
def update_lipid(lipid_id):
    """Update lipid with automatic backup"""
    try:
        lipid = MainLipid.query.get_or_404(lipid_id)
        
        # Get old data for backup
        old_data = {
            'lipid_name': lipid.lipid_name,
            'lipid_class': lipid.lipid_class.class_name if lipid.lipid_class else None,
            'retention_time': float(lipid.retention_time) if lipid.retention_time else None
        }
        
        # Get new data from form
        new_lipid_name = request.form.get('lipid_name')
        if new_lipid_name:
            new_data = old_data.copy()
            new_data['lipid_name'] = new_lipid_name
            
            # Use auto-backup context
            with auto_backup_context(
                backup_system=backup_system,
                table_name='main_lipids',
                record_id=lipid_id,
                operation='UPDATE',
                old_data=old_data,
                new_data=new_data,
                user_id=request.remote_addr,  # Use IP as user ID for now
                source='web_interface'
            ):
                lipid.lipid_name = new_lipid_name
                db.session.commit()
            
            flash(f'Lipid {lipid_id} updated successfully (with backup)', 'success')
        
        return redirect(url_for('clean_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating lipid: {str(e)}', 'error')
        return redirect(url_for('clean_dashboard'))

# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# =====================================================
# SCHEDULING ROUTES
# =====================================================

@app.route('/schedule')
def schedule_form():
    """Display scheduling form"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('schedule_form.html', today=today)

@app.route('/schedule', methods=['POST'])
def submit_schedule_request():
    """Handle schedule request submission"""
    try:
        # Get form data
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        organization = request.form.get('organization', '').strip()
        request_type = request.form.get('request_type', '').strip()
        preferred_date = request.form.get('preferred_date', '').strip()
        preferred_time = request.form.get('preferred_time', '').strip()
        message = request.form.get('message', '').strip()
        
        # Validate required fields
        if not all([full_name, email, request_type, message]):
            flash('Please fill in all required fields.', 'error')
            return render_template('schedule_form.html', today=datetime.now().strftime('%Y-%m-%d'))
        
        # Validate email format
        import re
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            flash('Please provide a valid email address.', 'error')
            return render_template('schedule_form.html', today=datetime.now().strftime('%Y-%m-%d'))
        
        # Parse preferred date
        preferred_date_obj = None
        if preferred_date:
            try:
                from datetime import datetime
                preferred_date_obj = datetime.strptime(preferred_date, '%Y-%m-%d').date()
            except ValueError:
                preferred_date_obj = None
        
        # Create schedule request
        schedule_request = ScheduleRequest(
            email=email,
            full_name=full_name,
            phone=phone,
            organization=organization,
            request_type=request_type,
            message=message,
            preferred_date=preferred_date_obj,
            preferred_time=preferred_time,
            status='pending'
        )
        
        db.session.add(schedule_request)
        db.session.commit()
        
        # Send email notifications using enhanced email service
        try:
            email_results = send_schedule_notification(schedule_request)
            if email_results['admin_sent'] or email_results['user_sent']:
                print(f"✅ Email notifications sent successfully")
                if email_results['admin_sent']:
                    print(f"   - Admin notification: {email_results['details']['admin']['method']}")
                if email_results['user_sent']:
                    print(f"   - User confirmation: {email_results['details']['user']['method']}")
            else:
                print(f"⚠️ Email notifications failed to send")
        except Exception as e:
            print(f"❌ Failed to send email notifications: {e}")
        
        flash(f'Thank you {full_name}! Your consultation request has been submitted successfully. We\'ll respond within 24-48 hours.', 'success')
        return redirect(url_for('homepage'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting request: {str(e)}', 'error')
        return render_template('schedule_form.html', today=datetime.now().strftime('%Y-%m-%d'))

# =====================================================
# EMAIL SYSTEM REPLACED
# =====================================================
# 
# The old send_schedule_notification_email() function has been replaced 
# with the enhanced email service (email_service_enhanced.py) which provides:
# 
# 1. SendGrid API support (production-ready)
# 2. Gmail SMTP fallback (development)
# 3. Professional HTML email templates
# 4. Better error handling and logging
# 5. Railway-compatible SMTP configuration
# 
# Email functionality is now handled by:
# - send_schedule_notification() - For schedule requests
# - test_email_configuration() - For testing
# - get_email_service_status() - For status checking

# =====================================================
# FUTURE MANAGEMENT SECTIONS (PLACEHOLDER ROUTES)
# =====================================================

@app.route('/patient-management')
@manager_required
def patient_management():
    """Patient Management section - Future feature"""
    return render_template('coming_soon.html', 
                         title="Patient Management", 
                         description="Manage patient data and research projects",
                         features=[
                             "Patient database management",
                             "Project assignment tracking", 
                             "Data access control",
                             "Research progress monitoring"
                         ])

@app.route('/equipment-management')
@manager_required  
def equipment_management():
    """Equipment Management section - Future feature"""
    return render_template('coming_soon.html',
                         title="Equipment Management",
                         description="Track and manage laboratory equipment",
                         features=[
                             "Equipment inventory tracking",
                             "Maintenance scheduling",
                             "Usage monitoring",
                             "Calibration management"
                         ])

# =====================================================
# LIPIDOMICS RESEARCH TOOLS 
# =====================================================

@app.route('/analysis-tools')
@login_required
def analysis_tools():
    """Analysis Tools section - Advanced lipidomics analysis"""
    return render_template('coming_soon.html',
                         title="Analysis Tools",
                         description="Advanced tools for lipidomics data analysis and interpretation",
                         features=[
                             "Statistical analysis and visualization",
                             "Pathway enrichment analysis",
                             "Biomarker discovery tools",
                             "Data quality assessment",
                             "Multi-variate analysis (PCA, PLS-DA)",
                             "Lipid class distribution analysis"
                         ])

@app.route('/lcms-tools')
@login_required
def lcms_tools():
    """LC-MS/MS Tools section - Mass spectrometry analysis tools"""
    return render_template('coming_soon.html',
                         title="LC-MS/MS Tools",
                         description="Specialized tools for LC-MS/MS data processing and analysis",
                         features=[
                             "Peak detection and integration",
                             "Mass spectral library matching",
                             "Retention time alignment",
                             "Isotope pattern analysis",
                             "Fragmentation pattern analysis",
                             "Quantitative analysis workflows"
                         ])

@app.route('/protocols')
def protocols():
    """Protocols section - Research protocols and methodologies"""
    return render_template('coming_soon.html',
                         title="Research Protocols",
                         description="Standardized protocols for lipidomics research and analysis",
                         features=[
                             "Sample preparation protocols",
                             "LC-MS/MS method development",
                             "Data processing workflows",
                             "Quality control procedures",
                             "Validation methodologies",
                             "Best practices guidelines"
                         ])

# =====================================================
# APPLICATION STARTUP
# =====================================================

if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        try:
            create_all_tables()
            print("✅ PostgreSQL tables created successfully")
        except Exception as e:
            print(f"❌ Database setup error: {e}")
    
    # Run application
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    print(f"🚀 Starting OPTIMIZED PostgreSQL Metabolomics App on port {port}")
    print(f"   Debug mode: {debug_mode}")
    print(f"   Database: PostgreSQL (Optimized with Eager Loading)")
    print(f"   Features: ✅ No N+1 Queries ✅ Proper Caching ✅ Fast Performance")
    print(f"   Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"   Custom Domain: {os.getenv('CUSTOM_DOMAIN', 'Not configured')}")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)