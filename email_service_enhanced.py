#!/usr/bin/env python3
"""
Enhanced Email Service for Metabolomics Platform
Supports both SendGrid (production) and Gmail SMTP (fallback) for maximum reliability
"""

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SendGrid integration
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent
    SENDGRID_AVAILABLE = True
    logger.info("✅ SendGrid library loaded successfully")
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning("⚠️ SendGrid library not available, falling back to SMTP only")

class EmailService:
    """
    Enhanced email service with multiple delivery methods:
    1. SendGrid API (Production) - Most reliable for cloud platforms
    2. Gmail SMTP (Fallback) - For development and backup
    """
    
    def __init__(self):
        self.sendgrid_api_key = None
        self.sendgrid_client = None
        self.smtp_config = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize email services based on available configuration"""
        # Initialize SendGrid if available
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        if self.sendgrid_api_key and SENDGRID_AVAILABLE:
            try:
                self.sendgrid_client = SendGridAPIClient(api_key=self.sendgrid_api_key)
                logger.info("✅ SendGrid API client initialized")
            except Exception as e:
                logger.error(f"❌ SendGrid initialization failed: {e}")
                self.sendgrid_client = None
        
        # Initialize SMTP config for fallback
        self.smtp_config = {
            'server': os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
            'port': int(os.getenv('MAIL_PORT', 587)),
            'username': os.getenv('MAIL_USERNAME'),
            'password': os.getenv('MAIL_PASSWORD'),
            'sender': os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME')
        }
        
        if self.smtp_config['username'] and self.smtp_config['password']:
            logger.info("✅ SMTP configuration loaded")
        else:
            logger.warning("⚠️ SMTP configuration incomplete")
    
    def _send_via_sendgrid(self, subject, recipients, html_content, sender_email=None):
        """
        Send email using SendGrid API
        
        Args:
            subject (str): Email subject
            recipients (str|list): Recipient email(s)
            html_content (str): HTML email content
            sender_email (str): Sender email (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sendgrid_client:
            logger.error("❌ SendGrid client not initialized")
            return False
        
        try:
            # Setup sender
            sender_email = sender_email or self.smtp_config['sender']
            sender_name = "Metabolomics Platform"
            from_email = From(sender_email, sender_name)
            
            # Handle single or multiple recipients
            if isinstance(recipients, str):
                recipients = [recipients]
            
            # Create and send email for each recipient (SendGrid best practice)
            for recipient in recipients:
                message = Mail(
                    from_email=from_email,
                    to_emails=To(recipient),
                    subject=Subject(subject),
                    html_content=HtmlContent(html_content)
                )
                
                response = self.sendgrid_client.send(message)
                logger.info(f"✅ SendGrid email sent to {recipient}, status: {response.status_code}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ SendGrid send failed: {e}")
            return False
    
    def _send_via_smtp(self, subject, recipients, html_content, sender_email=None):
        """
        Send email using Gmail SMTP (fallback method)
        
        Args:
            subject (str): Email subject
            recipients (str|list): Recipient email(s)
            html_content (str): HTML email content
            sender_email (str): Sender email (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.smtp_config['username'] or not self.smtp_config['password']:
            logger.error("❌ SMTP configuration missing")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"Metabolomics Platform <{sender_email or self.smtp_config['sender']}>"
            
            # Handle recipients
            if isinstance(recipients, list):
                msg['To'] = ", ".join(recipients)
                recipient_list = recipients
            else:
                msg['To'] = recipients
                recipient_list = [recipients]
            
            # Attach HTML content
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            logger.info(f"Attempting SMTP send to {recipient_list}")
            
            # Use proven SMTP sequence that works on Railway
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                # Railway-compatible SMTP sequence
                server.ehlo('metabolomics-platform.com')  # Custom hostname
                server.starttls()
                server.ehlo('metabolomics-platform.com')  # Re-identify after TLS
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
                
            logger.info(f"✅ SMTP email sent successfully to {recipient_list}")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP send failed: {e}")
            return False
    
    def send_email(self, subject, recipients, template, context, sender_email=None):
        """
        Send email using best available method (SendGrid first, SMTP fallback)
        
        Args:
            subject (str): Email subject
            recipients (str|list): Recipient email(s)
            template (str): Email template path
            context (dict): Template variables
            sender_email (str): Optional custom sender
        
        Returns:
            dict: Detailed results of send attempts
        """
        try:
            # Render email template
            html_content = render_template(template, **context)
            logger.info(f"📧 Sending email: '{subject}' to {recipients}")
            
            # Try SendGrid first (production method)
            if self.sendgrid_client:
                logger.info("🚀 Attempting SendGrid delivery...")
                if self._send_via_sendgrid(subject, recipients, html_content, sender_email):
                    return {
                        'success': True,
                        'method': 'sendgrid',
                        'message': 'Email sent successfully via SendGrid'
                    }
                else:
                    logger.warning("⚠️ SendGrid failed, trying SMTP fallback...")
            
            # Fallback to SMTP
            logger.info("📮 Attempting SMTP delivery...")
            if self._send_via_smtp(subject, recipients, html_content, sender_email):
                return {
                    'success': True,
                    'method': 'smtp',
                    'message': 'Email sent successfully via SMTP'
                }
            
            # Both methods failed
            return {
                'success': False,
                'method': 'none',
                'message': 'All email delivery methods failed'
            }
            
        except Exception as e:
            logger.error(f"❌ Email service error: {e}")
            return {
                'success': False,
                'method': 'error',
                'message': f'Email service error: {str(e)}'
            }

# Global email service instance
email_service = EmailService()

def send_email(subject, recipients, template, context, sender_email=None):
    """
    Convenience function for sending emails
    
    Args:
        subject (str): Email subject
        recipients (str|list): Recipient email(s)
        template (str): Email template path
        context (dict): Template variables
        sender_email (str): Optional custom sender
    
    Returns:
        bool: True if successful, False otherwise
    """
    result = email_service.send_email(subject, recipients, template, context, sender_email)
    return result['success']

def send_schedule_notification(schedule_request):
    """
    Send both admin notification and user confirmation for schedule requests
    
    Args:
        schedule_request: ScheduleRequest model instance
    
    Returns:
        dict: Results of both email attempts
    """
    results = {
        'admin_sent': False,
        'user_sent': False,
        'details': {}
    }
    
    # 1. Send notification to admin
    admin_email = email_service.smtp_config.get('username')
    if admin_email:
        admin_result = email_service.send_email(
            subject=f"New Consultation Request - {schedule_request.full_name}",
            recipients=[admin_email],
            template='email/schedule_admin_notification.html',
            context={'request': schedule_request}
        )
        results['admin_sent'] = admin_result['success']
        results['details']['admin'] = admin_result
    
    # 2. Send confirmation to user
    user_result = email_service.send_email(
        subject="Consultation Request Received - Metabolomics Platform",
        recipients=[schedule_request.email],
        template='email/schedule_user_confirmation.html',
        context={'request': schedule_request}
    )
    results['user_sent'] = user_result['success']
    results['details']['user'] = user_result
    
    return results

def test_email_configuration():
    """
    Test email configuration by sending a test email
    
    Returns:
        dict: Test results with details
    """
    admin_email = email_service.smtp_config.get('username')
    if not admin_email:
        return {
            'success': False,
            'message': 'No admin email configured for testing'
        }
    
    result = email_service.send_email(
        subject="Email Configuration Test - Metabolomics Platform",
        recipients=[admin_email],
        template='email/test_email.html',
        context={'test_time': 'Now'}
    )
    
    return result

def get_email_service_status():
    """
    Get status of available email services
    
    Returns:
        dict: Status of SendGrid and SMTP services
    """
    return {
        'sendgrid': {
            'available': bool(email_service.sendgrid_client),
            'api_key_configured': bool(email_service.sendgrid_api_key)
        },
        'smtp': {
            'available': bool(email_service.smtp_config['username'] and email_service.smtp_config['password']),
            'server': email_service.smtp_config['server'],
            'port': email_service.smtp_config['port']
        }
    }