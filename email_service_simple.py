#!/usr/bin/env python3
"""
Simplified Email Service for Metabolomics Platform
Uses only Gmail SMTP - proven to work on Railway
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

class SimpleEmailService:
    """
    Simple email service using only Gmail SMTP
    This is the proven method that works on Railway
    """
    
    def __init__(self):
        self.smtp_config = {
            'server': os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
            'port': int(os.getenv('MAIL_PORT', 587)),
            'username': os.getenv('MAIL_USERNAME'),
            'password': os.getenv('MAIL_PASSWORD'),
            'sender': os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME')
        }
        
        if self.smtp_config['username'] and self.smtp_config['password']:
            logger.info("✅ Gmail SMTP configuration loaded")
        else:
            logger.warning("⚠️ Gmail SMTP configuration incomplete")
    
    def send_email(self, subject, recipients, template, context, sender_email=None):
        """
        Send email using Gmail SMTP with the proven Railway method
        
        Args:
            subject (str): Email subject
            recipients (str|list): Recipient email(s)
            template (str): Email template path
            context (dict): Template variables
            sender_email (str): Optional custom sender
        
        Returns:
            dict: Detailed results of send attempt
        """
        if not self.smtp_config['username'] or not self.smtp_config['password']:
            return {
                'success': False,
                'method': 'smtp',
                'message': 'Gmail SMTP configuration missing'
            }
        
        try:
            # Render email template
            html_content = render_template(template, **context)
            logger.info(f"📧 Sending email: '{subject}' to {recipients}")
            
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
            
            logger.info(f"Attempting Gmail SMTP send to {recipient_list}")
            
            # Use the proven SMTP sequence that works on Railway
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                # Railway-compatible SMTP sequence
                server.ehlo('metabolomics-platform.com')  # Custom hostname
                server.starttls()
                server.ehlo('metabolomics-platform.com')  # Re-identify after TLS
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
                
            logger.info(f"✅ Gmail SMTP email sent successfully to {recipient_list}")
            return {
                'success': True,
                'method': 'gmail-smtp',
                'message': 'Email sent successfully via Gmail SMTP'
            }
            
        except Exception as e:
            logger.error(f"❌ Gmail SMTP send failed: {e}")
            return {
                'success': False,
                'method': 'gmail-smtp',
                'message': f'Gmail SMTP error: {str(e)}'
            }

# Global email service instance
email_service = SimpleEmailService()

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
        logger.info(f"Admin notification: {admin_result['message']}")
    
    # 2. Send confirmation to user
    user_result = email_service.send_email(
        subject="Consultation Request Received - Metabolomics Platform",
        recipients=[schedule_request.email],
        template='email/schedule_user_confirmation.html',
        context={'request': schedule_request}
    )
    results['user_sent'] = user_result['success']
    results['details']['user'] = user_result
    logger.info(f"User confirmation: {user_result['message']}")
    
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
    Get status of Gmail SMTP service
    
    Returns:
        dict: Status of Gmail SMTP service
    """
    return {
        'gmail_smtp': {
            'available': bool(email_service.smtp_config['username'] and email_service.smtp_config['password']),
            'server': email_service.smtp_config['server'],
            'port': email_service.smtp_config['port'],
            'username': email_service.smtp_config['username']
        }
    }