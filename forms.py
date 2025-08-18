"""
WTForms for the Metabolomics Platform
Proper form handling with built-in CSRF protection
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, Email, Optional
import re

class PasswordUpdateForm(FlaskForm):
    """Form for updating user passwords with proper CSRF protection"""
    
    current_password = PasswordField(
        'Current Password',
        validators=[Optional()],  # Optional because new users might not have a current password
        render_kw={"placeholder": "Enter your current password"}
    )
    
    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message="New password is required"),
            Length(min=8, message="Password must be at least 8 characters long")
        ],
        render_kw={"placeholder": "Enter your new password"}
    )
    
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message="Password confirmation is required"),
            EqualTo('new_password', message='Passwords must match')
        ],
        render_kw={"placeholder": "Confirm your new password"}
    )
    
    submit = SubmitField('Save Password')
    
    def validate_new_password(self, field):
        """Custom password strength validation"""
        password = field.data
        errors = []
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        if errors:
            from wtforms.validators import ValidationError
            raise ValidationError(". ".join(errors))

class ConsultationForm(FlaskForm):
    """Form for consultation requests with CSRF protection"""
    
    full_name = StringField(
        'Full Name',
        validators=[DataRequired(message="Full name is required")],
        render_kw={"placeholder": "Enter your full name"}
    )
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Please enter a valid email address")
        ],
        render_kw={"placeholder": "your.email@example.com"}
    )
    
    phone = StringField(
        'Phone Number',
        validators=[Optional()],
        render_kw={"placeholder": "+1 (555) 123-4567"}
    )
    
    message = TextAreaField(
        'Message',
        validators=[
            DataRequired(message="Message is required"),
            Length(min=10, message="Message must be at least 10 characters long")
        ],
        render_kw={"placeholder": "Please describe your consultation needs...", "rows": 5}
    )
    
    consent = BooleanField(
        'I consent to data processing',
        validators=[DataRequired(message="You must consent to data processing")]
    )
    
    submit = SubmitField('Submit Consultation Request')

class ContactForm(FlaskForm):
    """Generic contact form with CSRF protection"""
    
    name = StringField(
        'Name',
        validators=[DataRequired(message="Name is required")],
        render_kw={"placeholder": "Your name"}
    )
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message="Email is required"),
            Email(message="Please enter a valid email address")
        ],
        render_kw={"placeholder": "your.email@example.com"}
    )
    
    subject = StringField(
        'Subject',
        validators=[DataRequired(message="Subject is required")],
        render_kw={"placeholder": "Message subject"}
    )
    
    message = TextAreaField(
        'Message',
        validators=[
            DataRequired(message="Message is required"),
            Length(min=10, message="Message must be at least 10 characters long")
        ],
        render_kw={"placeholder": "Your message...", "rows": 6}
    )
    
    submit = SubmitField('Send Message')