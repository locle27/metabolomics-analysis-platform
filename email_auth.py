"""
Secure Email-Based Authentication System
Replaces OAuth with email verification for account activation
"""

import re
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash
from models_postgresql_optimized import db, User, VerificationToken

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def is_valid_email(email):
    """Validate email format"""
    return EMAIL_REGEX.match(email) is not None

def is_strong_password(password):
    """Check password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def send_verification_email(user, token):
    """Send email verification email"""
    try:
        # Try Flask-Mail first
        from app import mail  # Import mail from main app
        
        verification_url = url_for('auth.verify_email', token=token.token, _external=True)
        
        msg = Message(
            subject='Verify Your Metabolomics Platform Account',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        
        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #2E4C92, #213671); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">Phenikaa University</h1>
                    <p style="color: #E0E6ED; margin: 5px 0 0 0;">Metabolomics Research Platform</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e0e6ed;">
                    <h2 style="color: #2E4C92; margin-top: 0;">Welcome to our platform!</h2>
                    
                    <p>Hello <strong>{user.username}</strong>,</p>
                    
                    <p>Thank you for registering with the Metabolomics Research Platform. To complete your account setup and start analyzing lipid chromatography data, please verify your email address.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background: linear-gradient(135deg, #2E4C92, #213671); 
                                  color: white; 
                                  padding: 12px 30px; 
                                  text-decoration: none; 
                                  border-radius: 25px; 
                                  font-weight: bold;
                                  display: inline-block;">
                            Verify Email Address
                        </a>
                    </div>
                    
                    <p style="color: #6C757D; font-size: 14px;">
                        <strong>Important:</strong> This verification link will expire in 24 hours. 
                        If you didn't create this account, please ignore this email.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #e0e6ed; margin: 30px 0;">
                    
                    <p style="color: #6C757D; font-size: 12px; text-align: center;">
                        Advanced Lipid Chromatography Data Analysis & Visualization Platform<br>
                        Phenikaa University Research Initiative
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        return True
        
    except Exception as e:
        logging.error(f"Failed to send verification email: {str(e)}")
        
        # Fallback: Try direct SMTP with hostname override
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Verify Your Metabolomics Platform Account'
            msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
            msg['To'] = user.email
            
            verification_url = url_for('auth.verify_email', token=token.token, _external=True)
            
            html_part = MIMEText(f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2E4C92;">Verify Your Account</h2>
                <p>Hello {user.username},</p>
                <p>Please click the link below to verify your email:</p>
                <a href="{verification_url}" style="background: #2E4C92; color: white; padding: 10px 20px; text-decoration: none;">Verify Email</a>
            </body>
            </html>
            """, 'html')
            
            msg.attach(html_part)
            
            # Send with hostname override
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.ehlo('metabolomics-platform.com')  # Override hostname
            server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            server.send_message(msg)
            server.quit()
            
            logging.info("Verification email sent via direct SMTP fallback")
            return True
            
        except Exception as e2:
            logging.error(f"Direct SMTP fallback also failed: {str(e2)}")
            return False

def send_password_reset_email(user, token):
    """Send password reset email using the same method as working scheduling system"""
    print(f"🔍 DEBUG: send_password_reset_email called for user {user.username}")
    try:
        # Use direct SMTP method (same as working scheduling system)
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Check if email is configured
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        print(f"🔍 DEBUG: Email config - Username: {mail_username}, Password: {'***' if mail_password else None}")
        
        if not mail_username or not mail_password:
            print("❌ DEBUG: Email not configured - cannot send password reset")
            logging.error("Email not configured - cannot send password reset")
            return False
        
        reset_url = url_for('auth.reset_password', token=token.token, _external=True)
        print(f"🔍 DEBUG: Reset URL generated: {reset_url}")
        
        # Create SMTP connection with EXACT SAME sequence as working scheduling system
        print("🔍 DEBUG: Creating SMTP connection...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        print("✅ DEBUG: SMTP server connected")
        
        # EXACT SEQUENCE FROM WORKING SCHEDULING SYSTEM:
        server.ehlo('metabolomics-platform.com')  # EHLO FIRST (before STARTTLS)
        print("✅ DEBUG: First EHLO sent with hostname override")
        
        server.starttls()
        print("✅ DEBUG: TLS started")
        
        server.ehlo('metabolomics-platform.com')  # EHLO AGAIN (after STARTTLS) - required by some servers
        print("✅ DEBUG: Second EHLO sent after STARTTLS")
        
        server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
        print("✅ DEBUG: Gmail login successful")
        
        # Admin notification
        admin_msg = MIMEMultipart()
        admin_msg['From'] = current_app.config['MAIL_USERNAME']
        admin_msg['To'] = current_app.config['MAIL_USERNAME']
        admin_msg['Subject'] = f"Password Reset Request - {user.username}"
        
        admin_body = f"""Password reset request submitted:

Username: {user.username}
Email: {user.email}
User ID: {user.id}
Reset URL: {reset_url}
Expires: {token.expires_at}

User requested password reset on Metabolomics Platform."""

        admin_msg.attach(MIMEText(admin_body, 'plain'))
        print("🔍 DEBUG: Sending admin notification...")
        server.sendmail(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_USERNAME'], admin_msg.as_string())
        print("✅ DEBUG: Admin notification sent successfully")
        logging.info(f"✅ Admin notification sent for password reset: {user.username}")
        
        # User password reset email
        print("🔍 DEBUG: Creating user password reset email...")
        user_msg = MIMEMultipart()
        user_msg['From'] = current_app.config['MAIL_USERNAME']
        user_msg['To'] = user.email
        user_msg['Subject'] = "Password Reset - Metabolomics Platform"
        
        user_body = f"""Dear {user.username},

We received a request to reset your password for your Metabolomics Research Platform account.

To reset your password, click the link below:
{reset_url}

IMPORTANT:
- This link will expire in 2 hours
- If you did not request this reset, please ignore this email
- Your password will remain unchanged until you use this link

If you have any questions, please contact our support team.

Best regards,
Metabolomics Research Team
Phenikaa University

Reset Request Details:
- Account: {user.username}
- Email: {user.email}
- Request Time: {token.created_at}"""

        user_msg.attach(MIMEText(user_body, 'plain', 'utf-8'))
        print(f"🔍 DEBUG: Sending password reset email to {user.email}...")
        server.sendmail(current_app.config['MAIL_USERNAME'], user.email, user_msg.as_string())
        print(f"✅ DEBUG: Password reset email sent successfully to {user.email}")
        logging.info(f"✅ Password reset email sent to: {user.email}")
        
        server.quit()
        print("✅ DEBUG: SMTP connection closed successfully")
        print("🎉 DEBUG: Password reset email process completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ DEBUG: Exception in send_password_reset_email: {e}")
        logging.error(f"Failed to send password reset email: {str(e)}")
        return False

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with email verification"""
    if current_user.is_authenticated:
        return redirect(url_for('clean_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long', 'error')
            return render_template('auth/register.html')
            
        if not is_valid_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('auth/register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
            
        is_strong, message = is_strong_password(password)
        if not is_strong:
            flash(message, 'error')
            return render_template('auth/register.html')
            
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
            
        try:
            # Create new user - TEMPORARILY SKIP EMAIL VERIFICATION
            user = User(
                username=username,
                email=email,
                is_active=True,   # Activate immediately (skip email verification)
                is_verified=True  # Mark as verified (skip email verification)
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Skip email verification temporarily
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
    """User login with rate limiting"""
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
            
        # Check if account is locked
        if user.is_account_locked():
            flash('Account temporarily locked due to multiple failed attempts. Please try again later.', 'error')
            return render_template('auth/login.html')
            
        # Verify password
        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.lock_account(30)  # Lock for 30 minutes
                flash('Too many failed attempts. Account locked for 30 minutes.', 'error')
            else:
                flash('Invalid username/email or password', 'error')
            db.session.commit()
            return render_template('auth/login.html')
            
        # Check if email is verified
        if not user.is_verified:
            flash('Please verify your email address before logging in. Check your inbox for verification link.', 'warning')
            return render_template('auth/login.html')
            
        # Successful login
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

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Email verification endpoint"""
    verification_token = VerificationToken.query.filter_by(
        token=token, 
        token_type='email_verification'
    ).first()
    
    if not verification_token or not verification_token.is_valid():
        flash('Invalid or expired verification link. Please request a new one.', 'error')
        return redirect(url_for('auth.login'))
        
    # Activate user account
    user = verification_token.user
    user.is_verified = True
    user.is_active = True
    verification_token.use_token()
    
    db.session.commit()
    
    flash('Email verified successfully! You can now log in to your account.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        print(f"🔍 DEBUG: Forgot password request for email: {email}")
        
        if not is_valid_email(email):
            print(f"❌ DEBUG: Invalid email format: {email}")
            flash('Please enter a valid email address', 'error')
            return render_template('auth/forgot_password.html')
            
        user = User.query.filter_by(email=email).first()
        print(f"🔍 DEBUG: User lookup result: {user}")
        
        if user:
            print(f"✅ DEBUG: User found - {user.username} (ID: {user.id})")
            try:
                # Generate password reset token (expires in 2 hours)
                token = user.generate_verification_token('password_reset', expires_delta=timedelta(hours=2))
                db.session.commit()
                print(f"✅ DEBUG: Token generated: {token.token[:20]}...")
                
                # Send password reset email
                print(f"📧 DEBUG: Attempting to send email to {user.email}")
                email_result = send_password_reset_email(user, token)
                print(f"📧 DEBUG: Email send result: {email_result}")
                
                if email_result:
                    print("✅ DEBUG: Email sent successfully!")
                    flash('Password reset instructions have been sent to your email address.', 'info')
                else:
                    print("❌ DEBUG: Email sending failed!")
                    flash('There was an error sending the password reset email. Please try again later.', 'error')
            except Exception as e:
                print(f"❌ DEBUG: Exception during password reset: {e}")
                flash('There was an error processing your request. Please try again later.', 'error')
        else:
            print(f"❌ DEBUG: No user found with email: {email}")
            # Check how many users exist and their emails
            all_users = User.query.all()
            print(f"🔍 DEBUG: Total users in database: {len(all_users)}")
            for u in all_users:
                print(f"   - {u.username}: {u.email or 'No email'}")
            
            # Don't reveal whether email exists or not - still show success message
            flash('Password reset instructions have been sent to your email address.', 'info')
            
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset with token"""
    # Verify the token
    verification_token = VerificationToken.query.filter_by(
        token=token, 
        token_type='password_reset'
    ).first()
    
    if not verification_token or not verification_token.is_valid():
        flash('Invalid or expired password reset link. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
        
    user = verification_token.user
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate new password
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html', token=token)
            
        is_strong, message = is_strong_password(new_password)
        if not is_strong:
            flash(message, 'error')
            return render_template('auth/reset_password.html', token=token)
            
        try:
            # Update password
            user.set_password(new_password)
            user.last_password_change = datetime.utcnow()
            
            # Mark token as used
            verification_token.use_token()
            
            # Reset failed login attempts
            user.unlock_account()
            
            # IMPORTANT: Mark user as verified when resetting password
            # This allows users to login after password reset
            user.is_verified = True
            user.is_active = True
            
            db.session.commit()
            
            flash('Password reset successfully! You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Password reset error: {str(e)}")
            flash('An error occurred while resetting your password. Please try again.', 'error')
            
    return render_template('auth/reset_password.html', token=token)

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