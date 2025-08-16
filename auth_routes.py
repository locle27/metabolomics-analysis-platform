"""
Authentication Routes for Metabolomics Platform
Standalone login system with registration, password reset
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models_postgresql_optimized import db, User
from auth_service import auth_service
from auth_forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, ChangePasswordForm, ProfileForm
from datetime import datetime
import os

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        success, message = auth_service.register_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            full_name=form.full_name.data,
            confirm_password=form.confirm_password.data
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Standalone user login page"""
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user, message = auth_service.login_user(
            username=form.username.data,
            password=form.password.data
        )
        
        if user:
            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect to next page or homepage
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('homepage'))
        else:
            flash(message, 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        success, message = auth_service.request_password_reset(form.email.data)
        flash(message, 'success' if success else 'error')
        
        if success:
            return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        success, message = auth_service.reset_password(
            token=token,
            new_password=form.password.data,
            confirm_password=form.confirm_password.data
        )
        
        flash(message, 'success' if success else 'error')
        
        if success:
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token)

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address"""
    if current_user.is_authenticated:
        flash('Your email is already verified.', 'info')
        return redirect(url_for('homepage'))
    
    success, message = auth_service.verify_email(token)
    flash(message, 'success' if success else 'error')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for logged-in users"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
        else:
            # Update password
            current_user.set_password(form.new_password.data)
            db.session.commit()
            
            flash('Password updated successfully!', 'success')
            return redirect(url_for('user_debug'))
    
    return render_template('auth/change_password.html', form=form)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    form = ProfileForm(original_email=current_user.email)
    
    if form.validate_on_submit():
        # Update user profile
        current_user.full_name = form.full_name.data
        
        # Check if email changed
        if form.email.data.lower() != current_user.email.lower():
            current_user.email = form.email.data.lower()
            current_user.email_verified = False  # Require re-verification
            
            # Generate new verification token
            verification_token = current_user.generate_verification_token()
            auth_service.send_verification_email(current_user, verification_token)
            
            flash('Profile updated! Please check your email to verify your new email address.', 'success')
        else:
            flash('Profile updated successfully!', 'success')
        
        db.session.commit()
        return redirect(url_for('auth.profile'))
    
    elif request.method == 'GET':
        # Pre-populate form with current user data
        form.full_name.data = current_user.full_name
        form.email.data = current_user.email
    
    return render_template('auth/profile.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    user_name = current_user.full_name
    logout_user()
    flash(f'Goodbye {user_name}! You have been logged out successfully.', 'info')
    return redirect(url_for('homepage'))

# Error handlers for auth blueprint
@auth_bp.errorhandler(404)
def auth_not_found(error):
    """Handle 404 errors in auth routes"""
    flash('The requested page was not found.', 'error')
    return redirect(url_for('auth.login'))

@auth_bp.errorhandler(500)
def auth_server_error(error):
    """Handle 500 errors in auth routes"""
    db.session.rollback()
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('auth.login'))

# Utility route for testing email system
@auth_bp.route('/test-email')
def test_email():
    """Test email functionality (development only)"""
    import os
    if os.getenv('FLASK_ENV') != 'development':
        flash('This feature is only available in development mode.', 'error')
        return redirect(url_for('homepage'))
    
    try:
        from flask_mail import Message
        from app import mail
        
        msg = Message(
            subject='Test Email - Metabolomics Platform',
            sender=os.getenv('MAIL_DEFAULT_SENDER'),
            recipients=[os.getenv('MAIL_USERNAME')]  # Send to admin email
        )
        
        msg.html = """
        <h2>Email System Test</h2>
        <p>This is a test email from the Metabolomics Platform authentication system.</p>
        <p>If you receive this email, the email configuration is working correctly!</p>
        <p>Timestamp: {{ timestamp }}</p>
        """.replace('{{ timestamp }}', str(datetime.now()))
        
        mail.send(msg)
        flash('Test email sent successfully! Check your inbox.', 'success')
        
    except Exception as e:
        flash(f'Email test failed: {str(e)}', 'error')
    
    return redirect(url_for('homepage'))

# Add context processor for auth forms
@auth_bp.app_context_processor
def inject_auth_forms():
    """Make auth forms available in all templates"""
    return {
        'quick_login_form': LoginForm(),
        'auth_available': True
    }