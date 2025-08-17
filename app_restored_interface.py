#!/usr/bin/env python3
"""
RESTORED INTERFACE METABOLOMICS PLATFORM
Uses bulletproof deployment patterns with original Phenikaa University interface
All original templates and styling preserved
"""

import os
import sys
import json
import base64
import time
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps, lru_cache
from io import BytesIO
import traceback
import secrets
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

print("🚀 RESTORED INTERFACE METABOLOMICS PLATFORM STARTING")
print(f"🐍 Python: {sys.version}")
print(f"📁 Directory: {os.getcwd()}")
print(f"📡 Port: {os.getenv('PORT', '5000')}")
print("=" * 60)

# === GLOBAL FEATURE TRACKING ===
FEATURES = {
    'flask': False, 'database': False, 'models': False, 'charts': False,
    'authentication': False, 'email': False, 'templates': True, 'backup': False
}

STARTUP_ERRORS = []
AUTH_USERS = {}  # In-memory user store for demo
SCHEDULE_REQUESTS = []  # In-memory schedule storage

# === STEP 1: CORE FLASK (CRITICAL) ===
try:
    from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, session, make_response, get_flashed_messages
    FEATURES['flask'] = True
    print("✅ Flask core loaded")
except ImportError as e:
    print(f"❌ CRITICAL: Flask failed: {e}")
    sys.exit(1)

# === STEP 2: ENVIRONMENT SETUP ===
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment loaded")
except:
    print("⚠️ Environment loading failed - using defaults")

# === STEP 3: FLASK APP CREATION ===
app = Flask(__name__, 
    template_folder=Path(__file__).resolve().parent / "templates", 
    static_folder=Path(__file__).resolve().parent / "static"
)
app.secret_key = os.getenv('SECRET_KEY', 'restored-metabolomics-platform-secret-key')

# Railway proxy fix
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
    print("✅ Railway proxy configured")
except:
    print("⚠️ Proxy fix unavailable")

# === STEP 4: DATABASE SETUP ===
db = None
database_url = os.getenv('DATABASE_URL')

if database_url:
    try:
        from flask_sqlalchemy import SQLAlchemy
        from sqlalchemy import text, Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
        from sqlalchemy.orm import relationship
        
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True, 'pool_recycle': 300, 'echo': False
        }
        
        db = SQLAlchemy()
        db.init_app(app)
        
        # Test connection
        with app.app_context():
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                FEATURES['database'] = True
                print("✅ Database connected")
                
    except Exception as e:
        print(f"⚠️ Database failed: {e}")
        STARTUP_ERRORS.append(f"Database: {e}")
        db = None
else:
    print("⚠️ No DATABASE_URL - using in-memory storage")

# === STEP 5: DATABASE MODELS ===
if FEATURES['database']:
    try:
        # User Model
        class User(db.Model):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            email = Column(String(255), unique=True, nullable=False)
            full_name = Column(String(255), nullable=False)
            role = Column(String(50), default='user')
            password_hash = Column(String(255))
            created_at = Column(DateTime, default=datetime.utcnow)
            is_active = Column(Boolean, default=True)
            
            def is_authenticated(self): return True
            def is_active_user(self): return self.is_active
            def is_anonymous(self): return False
            def get_id(self): return str(self.id)
            def is_admin(self): return self.role == 'admin'
            def is_manager(self): return self.role in ['admin', 'manager']

        # Lipid Models
        class MainLipid(db.Model):
            __tablename__ = 'main_lipids'
            id = Column(Integer, primary_key=True)
            lipid_name = Column(String(255), nullable=False)
            api_code = Column(String(50))
            class_name = Column(String(100))
            retention_time = Column(Float)
            precursor_mass = Column(Float)
            product_mass = Column(Float)
            xic_data = Column(Text)
            created_at = Column(DateTime, default=datetime.utcnow)

        class AnnotatedIon(db.Model):
            __tablename__ = 'annotated_ions'
            id = Column(Integer, primary_key=True)
            lipid_id = Column(Integer, ForeignKey('main_lipids.id'))
            annotation = Column(String(255))
            integration_start = Column(Float)
            integration_end = Column(Float)
            integration_area = Column(Float)
            lipid = relationship("MainLipid", backref="annotations")

        class ScheduleRequest(db.Model):
            __tablename__ = 'schedule_requests'
            id = Column(Integer, primary_key=True)
            name = Column(String(255), nullable=False)
            email = Column(String(255), nullable=False)
            organization = Column(String(255))
            research_area = Column(String(255))
            message = Column(Text)
            preferred_date = Column(String(100))
            status = Column(String(50), default='pending')
            created_at = Column(DateTime, default=datetime.utcnow)

        # Create tables
        with app.app_context():
            db.create_all()
            print("✅ Database tables created")
            
        FEATURES['models'] = True
        
    except Exception as e:
        print(f"⚠️ Models failed: {e}")
        STARTUP_ERRORS.append(f"Models: {e}")

# === STEP 6: AUTHENTICATION SYSTEM ===
try:
    from flask_login import LoginManager, login_user, logout_user, login_required, current_user
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        if FEATURES['models']:
            return User.query.get(int(user_id))
        # Fallback to in-memory
        return AUTH_USERS.get(user_id)
    
    FEATURES['authentication'] = True
    print("✅ Authentication system loaded")
    
except Exception as e:
    print(f"⚠️ Authentication failed: {e}")
    STARTUP_ERRORS.append(f"Authentication: {e}")

# === STEP 7: EMAIL SYSTEM ===
def send_email(to_email, subject, html_content, text_content=None):
    """Send email with comprehensive error handling"""
    try:
        if not os.getenv('MAIL_USERNAME') or not os.getenv('MAIL_PASSWORD'):
            print("⚠️ Email credentials not configured")
            return False
            
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))
        msg['To'] = to_email
        
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        server = smtplib.SMTP(os.getenv('MAIL_SERVER', 'smtp.gmail.com'), int(os.getenv('MAIL_PORT', 587)))
        server.starttls()
        server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()
        
        FEATURES['email'] = True
        return True
        
    except Exception as e:
        print(f"⚠️ Email send failed: {e}")
        return False

# === UTILITY FUNCTIONS ===
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not FEATURES['authentication']:
            return redirect(url_for('auth.login'))
        if not (current_user.is_authenticated and current_user.is_admin()):
            flash('Admin access required.', 'error')
            return redirect(url_for('homepage'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_safe(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not FEATURES['authentication']:
            flash('Authentication system not available.', 'warning')
            return redirect(url_for('homepage'))
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# === CONTEXT PROCESSORS ===
@app.context_processor
def inject_features():
    """Make features available to all templates"""
    return dict(
        features=FEATURES,
        current_date=datetime.now().strftime('%Y-%m-%d'),
        platform_version="3.0.0-restored"
    )

# === MAIN ROUTES (Using Original Template Names) ===

@app.route('/health')
def health_check():
    """Railway health check - guaranteed to work"""
    return jsonify({
        "status": "healthy",
        "message": "Restored interface metabolomics platform operational",
        "timestamp": datetime.now().isoformat(),
        "features": FEATURES,
        "version": "3.0.0-restored-interface"
    }), 200

@app.route('/')
def homepage():
    """Homepage using original template"""
    try:
        # Homepage data
        homepage_data = {
            'stats': {
                'total_lipids': 0,
                'total_annotations': 0,
                'total_classes': 0,
                'database_status': 'disconnected'
            },
            'recent_lipids': [],
            'features_available': FEATURES,
            'news': [
                {
                    'title': 'Interface Restored Successfully',
                    'summary': 'Original Phenikaa University interface restored with bulletproof deployment.',
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
            ]
        }
        
        # Try to get database stats if available
        if FEATURES['models']:
            try:
                homepage_data['stats']['total_lipids'] = MainLipid.query.count()
                homepage_data['stats']['total_annotations'] = AnnotatedIon.query.count()
                homepage_data['stats']['database_status'] = 'connected'
                homepage_data['recent_lipids'] = MainLipid.query.limit(3).all()
            except Exception as e:
                print(f"⚠️ Database stats failed: {e}")
        
        return render_template('homepage.html', data=homepage_data)
        
    except Exception as e:
        print(f"⚠️ Homepage template failed: {e}")
        # Fallback
        return f"<h1>Metabolomics Platform</h1><p>Status: Operational</p><p>Interface: Restored</p>"

@app.route('/dashboard')
@app.route('/clean-dashboard')
def clean_dashboard():
    """Main lipid selection dashboard using original template"""
    try:
        lipids = []
        if FEATURES['models']:
            try:
                lipids = MainLipid.query.limit(50).all()
            except:
                pass
        
        return render_template('clean_dashboard.html', lipids=lipids)
        
    except Exception as e:
        print(f"⚠️ Dashboard template failed: {e}")
        return render_template('coming_soon.html', 
            title="Lipid Dashboard", 
            message="Dashboard loading with original interface..."
        )

@app.route('/dual-chart-view')
@app.route('/dual-chart-view/<int:lipid_id>')
def dual_chart_view(lipid_id=None):
    """Interactive dual chart analysis using original template"""
    try:
        lipid = None
        if lipid_id and FEATURES['models']:
            try:
                lipid = MainLipid.query.get(lipid_id)
            except:
                pass
        
        return render_template('dual_chart_view.html', 
            lipid=lipid, 
            lipid_id=lipid_id
        )
        
    except Exception as e:
        print(f"⚠️ Chart template failed: {e}")
        return render_template('coming_soon.html', 
            title="Interactive Charts", 
            message="Chart system loading with original interface..."
        )

@app.route('/browse-lipids')
def browse_lipids():
    """Browse and search lipids using original template"""
    try:
        return render_template('browse_lipids.html')
    except Exception as e:
        print(f"⚠️ Browse template failed: {e}")
        return render_template('coming_soon.html', 
            title="Browse Lipids", 
            message="Browse system loading..."
        )

@app.route('/schedule', methods=['GET', 'POST'])
@app.route('/schedule-form', methods=['GET', 'POST'])
def schedule_form():
    """Schedule consultation using original template"""
    if request.method == 'POST':
        try:
            # Collect form data
            name = request.form.get('name')
            email = request.form.get('email')
            organization = request.form.get('organization')
            research_area = request.form.get('research_area')
            message = request.form.get('message')
            preferred_date = request.form.get('preferred_date')
            
            # Save to database or memory
            if FEATURES['models']:
                schedule_request = ScheduleRequest(
                    name=name, email=email, organization=organization,
                    research_area=research_area, message=message, preferred_date=preferred_date
                )
                db.session.add(schedule_request)
                db.session.commit()
            else:
                SCHEDULE_REQUESTS.append({
                    'name': name, 'email': email, 'organization': organization,
                    'research_area': research_area, 'message': message, 
                    'preferred_date': preferred_date, 'created_at': datetime.now()
                })
            
            # Send notification email
            if FEATURES['email']:
                admin_email = os.getenv('MAIL_DEFAULT_SENDER', 'admin@metabolomics-platform.com')
                send_email(
                    admin_email,
                    f"New Consultation Request - {name}",
                    f"""
                    <h2>New Consultation Request</h2>
                    <p><strong>Name:</strong> {name}</p>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Organization:</strong> {organization}</p>
                    <p><strong>Research Area:</strong> {research_area}</p>
                    <p><strong>Preferred Date:</strong> {preferred_date}</p>
                    <p><strong>Message:</strong></p>
                    <p>{message}</p>
                    """
                )
            
            flash('Consultation request submitted successfully! We will contact you soon.', 'success')
            return redirect(url_for('schedule_form'))
            
        except Exception as e:
            flash(f'Error submitting request: {e}', 'error')
    
    try:
        return render_template('schedule_form.html')
    except Exception as e:
        print(f"⚠️ Schedule template failed: {e}")
        return render_template('coming_soon.html', 
            title="Schedule Consultation", 
            message="Scheduling system loading..."
        )

# === ADMIN ROUTES ===

@app.route('/admin')
@app.route('/admin-dashboard')
def admin_dashboard():
    """Admin dashboard using original template"""
    try:
        stats = {
            'total_lipids': 0,
            'total_users': 0,
            'total_schedules': len(SCHEDULE_REQUESTS),
            'features_active': sum(FEATURES.values())
        }
        
        if FEATURES['models']:
            try:
                stats['total_lipids'] = MainLipid.query.count()
                stats['total_users'] = User.query.count()
                stats['total_schedules'] = ScheduleRequest.query.count()
            except:
                pass
        
        return render_template('admin_dashboard.html', stats=stats)
        
    except Exception as e:
        print(f"⚠️ Admin template failed: {e}")
        return render_template('coming_soon.html', 
            title="Admin Dashboard", 
            message="Admin system loading..."
        )

@app.route('/manage-lipids')
def manage_lipids():
    """Database management using original template"""
    try:
        return render_template('manage_lipids.html')
    except Exception as e:
        print(f"⚠️ Manage template failed: {e}")
        return render_template('coming_soon.html', 
            title="Database Management", 
            message="Management system loading..."
        )

@app.route('/backup-management')
def backup_management():
    """Backup system using original template"""
    try:
        return render_template('backup_management.html')
    except Exception as e:
        print(f"⚠️ Backup template failed: {e}")
        return render_template('coming_soon.html', 
            title="Backup Management", 
            message="Backup system loading..."
        )

@app.route('/admin-stats')
def admin_stats():
    """System statistics using original template"""
    try:
        return render_template('admin_stats.html')
    except Exception as e:
        print(f"⚠️ Stats template failed: {e}")
        return render_template('coming_soon.html', 
            title="System Statistics", 
            message="Statistics loading..."
        )

# === FUTURE FEATURE ROUTES ===

@app.route('/analysis-tools')
def analysis_tools():
    """Analysis tools placeholder"""
    return render_template('coming_soon.html', 
        title="Analysis Tools", 
        message="Advanced analysis tools coming soon..."
    )

@app.route('/lcms-tools')
def lcms_tools():
    """LC-MS/MS tools placeholder"""
    return render_template('coming_soon.html', 
        title="LC-MS/MS Tools", 
        message="LC-MS/MS processing tools coming soon..."
    )

@app.route('/protocols')
def protocols():
    """Protocols placeholder"""
    return render_template('coming_soon.html', 
        title="Research Protocols", 
        message="Research protocols and methodologies coming soon..."
    )

@app.route('/patient-management')
def patient_management():
    """Patient management placeholder"""
    return render_template('coming_soon.html', 
        title="Patient Management", 
        message="Patient data management system coming soon..."
    )

@app.route('/equipment-management')
def equipment_management():
    """Equipment management placeholder"""
    return render_template('coming_soon.html', 
        title="Equipment Management", 
        message="Laboratory equipment tracking coming soon..."
    )

# === AUTHENTICATION BLUEPRINT (Simple fallback) ===

from flask import Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login form"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Demo login
        if email == 'admin@demo.com' and password == 'admin':
            if FEATURES['authentication']:
                # Create demo user
                demo_user = type('User', (), {
                    'id': 1, 'email': email, 'full_name': 'Demo Admin', 'role': 'admin',
                    'is_authenticated': lambda: True, 'is_active': lambda: True,
                    'is_anonymous': lambda: False, 'get_id': lambda: '1',
                    'is_admin': lambda: True, 'is_manager': lambda: True
                })()
                
                AUTH_USERS['1'] = demo_user
                login_user(demo_user)
                flash('Demo login successful!', 'success')
                return redirect(url_for('homepage'))
            else:
                session['demo_user'] = True
                flash('Demo session started (authentication system unavailable)', 'warning')
                return redirect(url_for('homepage'))
        else:
            flash('Invalid credentials. Use admin@demo.com / admin for demo access.', 'error')
    
    try:
        return render_template('auth/login.html')
    except:
        # Fallback login template
        return f'''
        <h2>Login</h2>
        <form method="POST">
            Email: <input type="email" name="email" required><br>
            Password: <input type="password" name="password" required><br>
            <button type="submit">Login</button>
        </form>
        <p>Demo: admin@demo.com / admin</p>
        <a href="{url_for('homepage')}">Back to Homepage</a>
        '''

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    if FEATURES['authentication'] and current_user.is_authenticated:
        logout_user()
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('homepage'))

@auth_bp.route('/profile')
@login_required_safe
def profile():
    """User profile"""
    try:
        return render_template('auth/profile.html')
    except:
        return f'<h2>Profile: {current_user.full_name}</h2><a href="{url_for('homepage')}">Back</a>'

# Register authentication blueprint
app.register_blueprint(auth_bp)

# === UTILITY ROUTES ===

@app.route('/debug')
def debug_info():
    """Debug information"""
    return jsonify({
        "platform": "Advanced Metabolomics Research Platform",
        "version": "3.0.0-restored-interface",
        "features": FEATURES,
        "startup_errors": STARTUP_ERRORS,
        "interface": "Original Phenikaa University Design Restored",
        "templates": "Using original template files",
        "environment": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "port": os.getenv('PORT', '5000'),
            "flask_env": os.getenv('FLASK_ENV', 'development')
        },
        "timestamp": datetime.now().isoformat()
    })

# === ERROR HANDLERS ===

@app.errorhandler(404)
def not_found(error):
    try:
        return render_template('404.html'), 404
    except:
        return f'<h1>404 - Page Not Found</h1><a href="{url_for("homepage")}">Return Home</a>', 404

@app.errorhandler(500)
def server_error(error):
    try:
        return render_template('500.html'), 500
    except:
        return f'<h1>500 - Server Error</h1><a href="{url_for("homepage")}">Return Home</a>', 500

# === APPLICATION STARTUP ===

print("🎯 RESTORED INTERFACE PLATFORM READY")
print(f"   Features active: {sum(FEATURES.values())}/{len(FEATURES)}")
print(f"   Database: {'✅' if FEATURES['database'] else '❌'}")
print(f"   Models: {'✅' if FEATURES['models'] else '❌'}")
print(f"   Authentication: {'✅' if FEATURES['authentication'] else '❌'}")
print(f"   Templates: ✅ Original Phenikaa University Interface")
print("=" * 60)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🌐 Starting restored interface platform on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

# For gunicorn
application = app