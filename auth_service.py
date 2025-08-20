"""
Authentication Service for Metabolomics Platform
Handles registration, login, password reset functionality
"""

import re
from datetime import datetime, timedelta
from flask import url_for, current_app
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
import secrets

class AuthService:
    """Comprehensive authentication service"""
    
    def __init__(self):
        self.password_min_length = 8
        self.password_complexity_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'
    
    def validate_email(self, email):
        """Validate email format"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None
    
    def validate_password(self, password):
        """Validate password strength"""
        errors = []
        
        if len(password) < self.password_min_length:
            errors.append(f"Password must be at least {self.password_min_length} characters long")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[@$!%*?&]', password):
            errors.append("Password must contain at least one special character (@$!%*?&)")
        
        return len(errors) == 0, errors
    
    def register_user(self, username, email, password, full_name, confirm_password):
        """Register new user with validation"""
        try:
            # Input validation
            if not username or not email or not password or not full_name:
                return False, "All fields are required"
            
            if password != confirm_password:
                return False, "Passwords do not match"
            
            if not self.validate_email(email):
                return False, "Invalid email format"
            
            is_valid_password, password_errors = self.validate_password(password)
            if not is_valid_password:
                return False, "; ".join(password_errors)
            
            # Check if username already exists
            existing_username = User.query.filter_by(username=username.lower()).first()
            if existing_username:
                return False, "This username is already taken"
            
            # Check if email already exists
            existing_email = User.query.filter_by(email=email.lower()).first()
            if existing_email:
                return False, "An account with this email already exists"
            
            # Check if this is the first user (make them admin)
            user_count = User.query.count()
            default_role = 'admin' if user_count == 0 else 'user'
            
            # Create new user
            user = User(
                username=username.lower(),
                email=email.lower(),
                full_name=full_name.strip(),
                role=default_role,
                is_active=True,
                auth_method='password',
                email_verified=False  # Require email verification
            )
            
            # Set password
            user.set_password(password)
            
            # Generate email verification token
            verification_token = user.generate_verification_token()
            
            # Save to database
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            self.send_verification_email(user, verification_token)
            
            return True, f"Account created successfully! Please check your email to verify your account."
            
        except Exception as e:
            db.session.rollback()
            return False, f"Registration failed: {str(e)}"
    
    def login_user(self, username, password):
        """Authenticate user login"""
        try:
            if not username or not password:
                return None, "Username and password are required"
            
            # Find user by username
            user = User.query.filter_by(username=username.lower()).first()
            if not user:
                return None, "Invalid username or password"
            
            # Check if account is locked
            if user.is_account_locked():
                return None, "Account is temporarily locked due to multiple failed login attempts. Please try again later."
            
            # Check if account is active
            if not user.is_active:
                return None, "Your account has been deactivated. Please contact support."
            
            # Verify password
            if not user.check_password(password):
                user.increment_failed_attempts()
                db.session.commit()
                return None, "Invalid username or password"
            
            # Check if email is verified (optional - can be disabled)
            if not user.email_verified and current_app.config.get('REQUIRE_EMAIL_VERIFICATION', False):
                return None, "Please verify your email address before logging in. Check your inbox for the verification link."
            
            # Successful login
            user.reset_failed_attempts()
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            return user, "Login successful"
            
        except Exception as e:
            return None, f"Login failed: {str(e)}"
    
    def request_password_reset(self, email):
        """Request password reset token"""
        try:
            user = User.query.filter_by(email=email.lower()).first()
            if not user:
                # Don't reveal if email exists for security
                return True, "If an account with this email exists, you will receive a password reset link."
            
            # Generate reset token
            reset_token = user.generate_reset_token()
            db.session.commit()
            
            # Send reset email
            self.send_password_reset_email(user, reset_token)
            
            return True, "If an account with this email exists, you will receive a password reset link."
            
        except Exception as e:
            return False, f"Password reset request failed: {str(e)}"
    
    def reset_password(self, token, new_password, confirm_password):
        """Reset password with token"""
        try:
            if new_password != confirm_password:
                return False, "Passwords do not match"
            
            is_valid_password, password_errors = self.validate_password(new_password)
            if not is_valid_password:
                return False, "; ".join(password_errors)
            
            # Find user by token
            user = User.query.filter_by(password_reset_token=token).first()
            if not user:
                return False, "Invalid or expired reset token"
            
            # Verify token
            if not user.verify_reset_token(token):
                return False, "Invalid or expired reset token"
            
            # Update password
            user.set_password(new_password)
            user.clear_reset_token()
            user.reset_failed_attempts()  # Clear any failed attempts
            
            db.session.commit()
            
            return True, "Password updated successfully! You can now log in with your new password."
            
        except Exception as e:
            db.session.rollback()
            return False, f"Password reset failed: {str(e)}"
    
    def verify_email(self, token):
        """Verify email address with token"""
        try:
            user = User.query.filter_by(email_verification_token=token).first()
            if not user:
                return False, "Invalid verification token"
            
            if user.verify_email(token):
                db.session.commit()
                return True, "Email verified successfully! You can now log in."
            else:
                return False, "Invalid verification token"
                
        except Exception as e:
            return False, f"Email verification failed: {str(e)}"
    
    def send_verification_email(self, user, token):
        """Send email verification"""
        try:
            from app import mail  # Import mail instance
            
            verification_url = url_for('verify_email', token=token, _external=True)
            
            msg = Message(
                subject='Verify Your Email - Metabolomics Platform',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            
            msg.html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #2E4C92; text-align: center;">Welcome to Metabolomics Platform!</h2>
                    
                    <p>Hello <strong>{user.full_name}</strong>,</p>
                    
                    <p>Thank you for registering with our Metabolomics Research Platform. To complete your registration, please verify your email address by clicking the button below:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #2E4C92; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Verify Email Address
                        </a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 5px;">{verification_url}</p>
                    
                    <p>This verification link will expire in 24 hours for security reasons.</p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    
                    <p style="font-size: 12px; color: #666;">
                        If you didn't create an account with us, please ignore this email.<br>
                        This email was sent from the Metabolomics Research Platform.
                    </p>
                </div>
            </body>
            </html>
            """
            
            mail.send(msg)
            return True
            
        except Exception as e:
            print(f"Failed to send verification email: {e}")
            return False
    
    def send_password_reset_email(self, user, token):
        """Send password reset email"""
        try:
            from app import mail  # Import mail instance
            
            reset_url = url_for('reset_password', token=token, _external=True)
            
            msg = Message(
                subject='Password Reset - Metabolomics Platform',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            
            msg.html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #2E4C92; text-align: center;">Password Reset Request</h2>
                    
                    <p>Hello <strong>{user.full_name}</strong>,</p>
                    
                    <p>We received a request to reset your password for your Metabolomics Platform account. If you made this request, click the button below to reset your password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background-color: #E94B00; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 5px;">{reset_url}</p>
                    
                    <p><strong>This link will expire in 1 hour</strong> for security reasons.</p>
                    
                    <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    
                    <p style="font-size: 12px; color: #666;">
                        For security reasons, this link can only be used once.<br>
                        This email was sent from the Metabolomics Research Platform.
                    </p>
                </div>
            </body>
            </html>
            """
            
            mail.send(msg)
            return True
            
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
            return False

# Initialize service instance
auth_service = AuthService()