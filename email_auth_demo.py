#!/usr/bin/env python3
"""
DEMO VERSION of email_auth.py for Railway deployment
This version removes all SMTP/email functionality to avoid Railway deployment issues
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import logging
import secrets
from werkzeug.security import check_password_hash, generate_password_hash

# Import models
from models_postgresql_optimized import db, User, VerificationToken

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

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration - DEMO VERSION (auto-verified)"""
    if current_user.is_authenticated:
        return redirect(url_for('clean_dashboard'))
        
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
            
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
            
        try:
            # Create new user - DEMO VERSION: INSTANTLY VERIFIED
            user = User(
                username=username,
                email=email,
                is_active=True,   # DEMO: Instantly active
                is_verified=True  # DEMO: Instantly verified
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # DEMO: No email verification needed
            flash('Account created successfully! You can now log in immediately.', 'success')
            return redirect(url_for('auth.login'))
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login - DEMO VERSION"""
    if current_user.is_authenticated:
        return redirect(url_for('clean_dashboard'))
        
    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        if not username_or_email or not password:
            flash('Please enter both username/email and password', 'error')
            return render_template('auth/login.html')
            
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email.lower())
        ).first()
        
        if not user:
            flash('Invalid username/email or password', 'error')
            return render_template('auth/login.html')
            
        # Check if account is locked (if attribute exists)
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
            
        # DEMO: Skip email verification check for Railway deployment
        # if not user.is_verified:
        #     flash('Please verify your email address before logging in.', 'warning')
        #     return render_template('auth/login.html')
            
        # Successful login
        if hasattr(user, 'unlock_account'):
            user.unlock_account()  # Reset failed attempts
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=remember_me)
        flash('Welcome back!', 'success')
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('clean_dashboard'))
    
    return render_template('auth/login.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - DEMO VERSION (disabled for Railway)"""
    if request.method == 'POST':
        # DEMO: Just redirect to login with message
        flash('Password reset feature temporarily disabled for deployment. Please contact administrator.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset - DEMO VERSION (disabled for Railway)"""
    flash('Password reset feature temporarily disabled for deployment. Please contact administrator.', 'info')
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

# Error handlers
@auth_bp.errorhandler(429)
def ratelimit_handler(e):
    return render_template('auth/rate_limit.html'), 429