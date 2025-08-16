#!/usr/bin/env python3
"""
PRODUCTION VERSION of email_auth.py for Railway deployment
Full-featured authentication with email support and OAuth integration
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import logging
import secrets
import uuid
from werkzeug.security import check_password_hash, generate_password_hash
from urllib.parse import urlparse, urljoin

# Database models will be accessed from current app context to avoid SQLAlchemy binding issues
def get_db():
    """Get database instance from current app"""
    from flask import current_app
    return current_app.extensions['sqlalchemy']

def get_models():
    """Get database models from current app context"""
    from flask import current_app
    # Get models from the main app's context
    app_globals = vars(current_app)
    User = None
    VerificationToken = None
    
    # Try to get User model from various sources
    try:
        # First try: get from main app globals
        for name, obj in app_globals.items():
            if hasattr(obj, '__tablename__'):
                if getattr(obj, '__tablename__', None) == 'users':
                    User = obj
                elif getattr(obj, '__tablename__', None) == 'verification_tokens':
                    VerificationToken = obj
        
        # Fallback: import from models file
        if not User or not VerificationToken:
            from models_postgresql_optimized import User as UserModel, VerificationToken as TokenModel
            User = User or UserModel
            VerificationToken = VerificationToken or TokenModel
            
    except Exception:
        # Final fallback: use models_postgresql_optimized
        from models_postgresql_optimized import User as UserModel, VerificationToken as TokenModel
        User = UserModel
        VerificationToken = TokenModel
    
    return User, VerificationToken

# Import simplified email service
from email_service_simple import send_email, email_service

# Create blueprint
auth_bp = Blueprint('auth', __name__)

def is_strong_password(password):
    """Check if password meets strength requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not has_upper:
        return False, "Password must contain at least one uppercase letter"
    if not has_lower:
        return False, "Password must contain at least one lowercase letter"
    if not has_digit:
        return False, "Password must contain at least one number"
    if not has_special:
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def is_safe_url(target):
    """Check if URL is safe for redirect"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def create_verification_token(user, token_type='email_verification'):
    """Create a verification token for user"""
    # Get database and models from current app context
    db = get_db()
    User, VerificationToken = get_models()
    
    # Clean up any existing tokens of this type
    with db.session.begin():
        db.session.query(VerificationToken).filter_by(
            user_id=user.id, 
            token_type=token_type,
            is_used=False
        ).delete()
        
        token = VerificationToken(
            user_id=user.id,
            token=secrets.token_urlsafe(32),
            token_type=token_type,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.session.add(token)
        db.session.commit()
        return token

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with email verification"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
            
        is_strong, message = is_strong_password(password)
        if not is_strong:
            flash(message, 'error')
            return render_template('auth/register.html')
            
        # Get database and models from current app context
        db = get_db()
        User, VerificationToken = get_models()
        
        if db.session.query(User).filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
            
        if db.session.query(User).filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
            
        try:
            # Create new user (initially unverified)
            user = User(
                username=username,
                email=email,
                is_active=True,   # Active but unverified
                is_verified=False  # Email verification required
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.flush()  # Get user.id
            
            # Create email verification token
            token = create_verification_token(user, 'email_verification')
            
            # Send verification email
            verification_url = url_for('auth.verify_email', token=token.token, _external=True)
            email_sent = send_email(
                subject="Verify Your Email - Metabolomics Platform",
                recipients=[email],
                template='email/email_verification.html',
                context={
                    'user': user,
                    'verification_url': verification_url,
                    'platform_name': 'Metabolomics Platform'
                }
            )
            
            db.session.commit()
            
            if email_sent:
                flash('Account created! Please check your email to verify your account.', 'success')
            else:
                flash('Account created, but verification email failed to send. Please contact support.', 'warning')
                
            return redirect(url_for('auth.login'))
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Email verification handler"""
    try:
        verification_token = VerificationToken.query.filter_by(
            token=token,
            token_type='email_verification',
            is_used=False
        ).first()
        
        if not verification_token:
            flash('Invalid or expired verification link', 'error')
            return redirect(url_for('auth.login'))
            
        if verification_token.expires_at < datetime.utcnow():
            flash('Verification link has expired. Please request a new one.', 'error')
            return redirect(url_for('auth.login'))
            
        # Verify the user
        user = verification_token.user
        user.is_verified = True
        verification_token.is_used = True
        verification_token.used_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Email verification error: {str(e)}")
        flash('An error occurred during verification. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with OAuth support"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        if not username_or_email or not password:
            flash('Please enter both username/email and password', 'error')
            return render_template('auth/login.html')
            
        # Get database and models from current app context
        db = get_db()
        User, VerificationToken = get_models()
        
        # Find user by username or email
        user = db.session.query(User).filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email.lower())
        ).first()
        
        if not user:
            flash('Invalid username/email or password', 'error')
            return render_template('auth/login.html')
            
        # Check if account is locked
        if hasattr(user, 'is_account_locked') and user.is_account_locked():
            flash('Account temporarily locked due to multiple failed attempts. Please try again later.', 'error')
            return render_template('auth/login.html')
            
        # Verify password
        if not user.check_password(password):
            if hasattr(user, 'failed_login_attempts'):
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    if hasattr(user, 'lock_account'):
                        user.lock_account(30)  # Lock for 30 minutes
                    flash('Too many failed attempts. Account locked for 30 minutes.', 'error')
                else:
                    flash('Invalid username/email or password', 'error')
            else:
                flash('Invalid username/email or password', 'error')
            db.session.commit()
            return render_template('auth/login.html')
            
        # Check email verification (production requirement)
        if not user.is_verified and not user.oauth_provider:
            flash('Please verify your email address before logging in. Check your inbox.', 'warning')
            return render_template('auth/login.html')
            
        # Successful login
        if hasattr(user, 'unlock_account'):
            user.unlock_account()  # Reset failed attempts
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=remember_me)
        flash('Welcome back!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for('dashboard'))
    
    return render_template('auth/login.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password with email reset"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address', 'error')
            return render_template('auth/forgot_password.html')
            
        try:
            # Get database and models from current app context
            db = get_db()
            User, VerificationToken = get_models()
            
            # Query user using the correct database instance
            with db.session.begin():
                user = db.session.query(User).filter_by(email=email).first()
                
        except Exception as e:
            current_app.logger.error(f"Database error: {e}")
            flash('Database error. Please try again.', 'error')
            return render_template('auth/forgot_password.html')
        
        if user:
            try:
                # Create password reset token
                token = create_verification_token(user, 'password_reset')
                
                # Send reset email
                reset_url = url_for('auth.reset_password', token=token.token, _external=True)
                email_sent = send_email(
                    subject="Password Reset - Metabolomics Platform",
                    recipients=[email],
                    template='email/password_reset.html',
                    context={
                        'user': user,
                        'reset_url': reset_url,
                        'platform_name': 'Metabolomics Platform',
                        'expires_hours': 24
                    }
                )
                
                if email_sent:
                    flash('Password reset instructions sent to your email', 'success')
                else:
                    flash('Failed to send reset email. Please try again or contact support.', 'error')
                    
            except Exception as e:
                logging.error(f"Password reset error: {str(e)}")
                flash('An error occurred. Please try again.', 'error')
        else:
            # Don't reveal if email exists - security best practice
            flash('If an account with that email exists, reset instructions have been sent', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset with token"""
    try:
        # Get database and models from current app context
        db = get_db()
        User, VerificationToken = get_models()
        
        verification_token = db.session.query(VerificationToken).filter_by(
            token=token,
            token_type='password_reset',
            is_used=False
        ).first()
        
        if not verification_token:
            flash('Invalid or expired reset link', 'error')
            return redirect(url_for('auth.forgot_password'))
            
        if verification_token.expires_at < datetime.utcnow():
            flash('Reset link has expired. Please request a new one.', 'error')
            return redirect(url_for('auth.forgot_password'))
            
        if request.method == 'POST':
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if new_password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('auth/reset_password.html', token=token)
                
            is_strong, message = is_strong_password(new_password)
            if not is_strong:
                flash(message, 'error')
                return render_template('auth/reset_password.html', token=token)
                
            # Update password
            user = db.session.query(User).filter_by(id=verification_token.user_id).first()
            if user:
                user.set_password(new_password)
                user.last_password_change = datetime.utcnow()
                verification_token.is_used = True
                verification_token.used_at = datetime.utcnow()
                
                db.session.commit()
                
                flash('Password reset successfully! You can now log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('User not found', 'error')
                return redirect(url_for('auth.forgot_password'))
            
        return render_template('auth/reset_password.html', token=token)
        
    except Exception as e:
        try:
            db = get_db()
            db.session.rollback()
        except:
            pass
        logging.error(f"Password reset error: {str(e)}")
        flash('An error occurred during password reset. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password'))

@auth_bp.route('/oauth-success')
def oauth_success():
    """OAuth success handler"""
    if current_user.is_authenticated:
        flash('Successfully logged in with Google!', 'success')
        next_page = session.pop('oauth_next', None)
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for('dashboard'))
    else:
        flash('OAuth login failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for logged-in user"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # OAuth users can't change password
        if current_user.oauth_provider:
            flash('OAuth users cannot change password. Please use your Google account settings.', 'info')
            return render_template('auth/change_password.html')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return render_template('auth/change_password.html')
            
        # Validate new password
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('auth/change_password.html')
            
        is_strong, message = is_strong_password(new_password)
        if not is_strong:
            flash(message, 'error')
            return render_template('auth/change_password.html')
            
        try:
            # Update password
            current_user.set_password(new_password)
            current_user.last_password_change = datetime.utcnow()
            db.session.commit()
            
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Password change error: {str(e)}")
            flash('An error occurred while changing password. Please try again.', 'error')
            
    return render_template('auth/change_password.html')

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend email verification"""
    email = request.form.get('email', '').strip().lower()
    
    if not email:
        flash('Please enter your email address', 'error')
        return redirect(url_for('auth.login'))
        
    # Get database and models from current app context
    db = get_db()
    User, VerificationToken = get_models()
    
    user = db.session.query(User).filter_by(email=email, is_verified=False).first()
    
    if user:
        try:
            # Create new verification token
            token = create_verification_token(user, 'email_verification')
            
            # Send verification email
            verification_url = url_for('auth.verify_email', token=token.token, _external=True)
            email_sent = send_email(
                subject="Verify Your Email - Metabolomics Platform",
                recipients=[email],
                template='email/email_verification.html',
                context={
                    'user': user,
                    'verification_url': verification_url,
                    'platform_name': 'Metabolomics Platform'
                }
            )
            
            if email_sent:
                flash('Verification email sent! Please check your inbox.', 'success')
            else:
                flash('Failed to send verification email. Please try again.', 'error')
                
        except Exception as e:
            logging.error(f"Resend verification error: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
    else:
        flash('Email not found or already verified', 'info')
    
    return redirect(url_for('auth.login'))

# Error handlers
@auth_bp.errorhandler(429)
def ratelimit_handler(e):
    return render_template('auth/rate_limit.html'), 429