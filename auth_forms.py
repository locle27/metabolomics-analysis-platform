"""
WTForms for Authentication
Forms for registration, login, password reset
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models_postgresql_optimized import User

class RegistrationForm(FlaskForm):
    """User registration form with validation"""
    
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=20, message="Username must be between 3 and 20 characters")
    ])
    
    full_name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required"),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters")
    ])
    
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        Length(max=255, message="Email must be less than 255 characters")
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    
    terms_accepted = BooleanField('I agree to the Terms of Service and Privacy Policy', validators=[
        DataRequired(message="You must accept the terms and conditions")
    ])
    
    submit = SubmitField('Create Account')
    
    def validate_username(self, username):
        """Check if username is already taken"""
        import re
        
        # Check alphanumeric with underscores only
        if not re.match("^[a-zA-Z0-9_]+$", username.data):
            raise ValidationError('Username can only contain letters, numbers, and underscores')
        
        user = User.query.filter_by(username=username.data.lower()).first()
        if user:
            raise ValidationError('This username is already taken. Please choose a different username.')
    
    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('An account with this email already exists. Please use a different email or try logging in.')
    
    def validate_password(self, password):
        """Validate password complexity"""
        import re
        
        if not re.search(r'[a-z]', password.data):
            raise ValidationError('Password must contain at least one lowercase letter')
        
        if not re.search(r'[A-Z]', password.data):
            raise ValidationError('Password must contain at least one uppercase letter')
        
        if not re.search(r'\d', password.data):
            raise ValidationError('Password must contain at least one number')
        
        if not re.search(r'[@$!%*?&]', password.data):
            raise ValidationError('Password must contain at least one special character (@$!%*?&)')

class LoginForm(FlaskForm):
    """User login form"""
    
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=20, message="Username must be between 3 and 20 characters")
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required")
    ])
    
    remember_me = BooleanField('Keep me logged in')
    
    submit = SubmitField('Sign In')

class ForgotPasswordForm(FlaskForm):
    """Forgot password form"""
    
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address")
    ])
    
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    """Reset password form"""
    
    password = PasswordField('New Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    
    submit = SubmitField('Reset Password')
    
    def validate_password(self, password):
        """Validate password complexity"""
        import re
        
        if not re.search(r'[a-z]', password.data):
            raise ValidationError('Password must contain at least one lowercase letter')
        
        if not re.search(r'[A-Z]', password.data):
            raise ValidationError('Password must contain at least one uppercase letter')
        
        if not re.search(r'\d', password.data):
            raise ValidationError('Password must contain at least one number')
        
        if not re.search(r'[@$!%*?&]', password.data):
            raise ValidationError('Password must contain at least one special character (@$!%*?&)')

class ChangePasswordForm(FlaskForm):
    """Change password form for logged-in users"""
    
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message="Current password is required")
    ])
    
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required"),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your new password"),
        EqualTo('new_password', message="Passwords must match")
    ])
    
    submit = SubmitField('Change Password')
    
    def validate_new_password(self, new_password):
        """Validate password complexity"""
        import re
        
        if not re.search(r'[a-z]', new_password.data):
            raise ValidationError('Password must contain at least one lowercase letter')
        
        if not re.search(r'[A-Z]', new_password.data):
            raise ValidationError('Password must contain at least one uppercase letter')
        
        if not re.search(r'\d', new_password.data):
            raise ValidationError('Password must contain at least one number')
        
        if not re.search(r'[@$!%*?&]', new_password.data):
            raise ValidationError('Password must contain at least one special character (@$!%*?&)')

class ProfileForm(FlaskForm):
    """User profile update form"""
    
    full_name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required"),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters")
    ])
    
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        Length(max=255, message="Email must be less than 255 characters")
    ])
    
    submit = SubmitField('Update Profile')
    
    def __init__(self, original_email, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
    
    def validate_email(self, email):
        """Check if email is already taken by another user"""
        if email.data.lower() != self.original_email.lower():
            user = User.query.filter_by(email=email.data.lower()).first()
            if user:
                raise ValidationError('This email is already registered to another account.')