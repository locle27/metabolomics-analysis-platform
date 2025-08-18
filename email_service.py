#!/usr/bin/env python3
"""
Centralized Email Service for Metabolomics Platform
Robust SMTP handling that works reliably on Railway and other cloud platforms
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template

# Configure logging to see output in Railway logs
logging.basicConfig(level=logging.INFO)

def send_email(subject, recipients, template, context):
    """
    Reliably sends an email using the application's current configuration.
    This uses the robust SMTP connection logic that works on Railway.
    
    Args:
        subject (str): Email subject line
        recipients (str|list): Email address(es) to send to
        template (str): Path to email template (relative to templates/)
        context (dict): Variables to pass to the template
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    mail_username = current_app.config.get('MAIL_USERNAME')
    mail_password = current_app.config.get('MAIL_PASSWORD')
    mail_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = current_app.config.get('MAIL_PORT', 587)
    mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER', mail_username)

    if not mail_username or not mail_password:
        logging.error("Email configuration is missing (MAIL_USERNAME or MAIL_PASSWORD). Email not sent.")
        return False

    try:
        # Render beautiful HTML body from template
        html_body = render_template(template, **context)

        # Create message with proper encoding
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Metabolomics Platform <{mail_sender}>"
        
        # Handle both single email and list of emails
        if isinstance(recipients, list):
            msg['To'] = ", ".join(recipients)
            recipient_list = recipients
        else:
            msg['To'] = recipients
            recipient_list = [recipients]
        
        # Attach HTML content with UTF-8 encoding
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        logging.info(f"Attempting to send email to {recipient_list} with subject: '{subject}'")

        # Use the proven SMTP connection logic with hostname override
        # This sequence works reliably on Railway and other cloud platforms
        with smtplib.SMTP(mail_server, mail_port) as server:
            # First EHLO with custom hostname (fixes Railway hostname issues)
            server.ehlo('metabolomics-platform.com')
            logging.info("✅ First EHLO sent with hostname override")
            
            # Start TLS encryption
            server.starttls()
            logging.info("✅ TLS encryption started")
            
            # Second EHLO after TLS (required by some SMTP servers)
            server.ehlo('metabolomics-platform.com')
            logging.info("✅ Second EHLO sent after TLS")
            
            # Authenticate with Gmail
            server.login(mail_username, mail_password)
            logging.info("✅ Gmail authentication successful")
            
            # Send the message
            server.send_message(msg)
            logging.info(f"✅ Email sent successfully to {recipient_list}!")
            return True

    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"❌ SMTP Authentication Error: {e}")
        logging.error("Please check MAIL_USERNAME and MAIL_PASSWORD (ensure it's a Gmail App Password)")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logging.error(f"❌ SMTP Recipients Refused: {e}")
        logging.error("One or more recipient email addresses were rejected")
        return False
    except smtplib.SMTPServerDisconnected as e:
        logging.error(f"❌ SMTP Server Disconnected: {e}")
        logging.error("Connection to SMTP server was lost")
        return False
    except Exception as e:
        logging.error(f"❌ Unexpected error while sending email: {e}")
        return False

def send_schedule_notification(schedule_request):
    """
    OPTIMIZED: Send admin notification and user confirmation efficiently
    Reduced from 3 emails to 2 emails to minimize delays
    
    Args:
        schedule_request: ScheduleRequest model instance
    
    Returns:
        dict: Results of email attempts
    """
    results = {
        'admin_sent': False,
        'user_sent': False,
        'followup_sent': False  # Keeping for compatibility but not sending
    }
    
    mail_username = current_app.config.get('MAIL_USERNAME')
    mail_password = current_app.config.get('MAIL_PASSWORD')
    
    if not mail_username or not mail_password:
        logging.error("❌ Email configuration missing - notifications skipped")
        return results
    
    # OPTIMIZATION: Use a single SMTP connection for both emails
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from flask import render_template
        
        mail_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = current_app.config.get('MAIL_PORT', 587)
        mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER', mail_username)
        
        logging.info(f"🚀 OPTIMIZED: Sending emails for {schedule_request.full_name}")
        
        # Single SMTP connection for multiple emails (much faster!)
        with smtplib.SMTP(mail_server, mail_port) as server:
            # Setup connection once
            server.ehlo('metabolomics-platform.com')
            server.starttls()
            server.ehlo('metabolomics-platform.com')
            server.login(mail_username, mail_password)
            logging.info("✅ Single SMTP connection established")
            
            # 1. Send notifications to all configured recipients
            # CRITICAL: Ensure notification settings are loaded from database
            try:
                from app import ensure_notification_settings_loaded
                ensure_notification_settings_loaded()
            except Exception as e:
                logging.warning(f"⚠️ Could not ensure notification settings loaded: {e}")
            
            notification_recipients = current_app.config.get('NOTIFICATION_EMAILS', [])
            
            # If no recipients configured, fallback to default admin email
            if not notification_recipients:
                notification_recipients = [mail_username] if mail_username else []
                
            if notification_recipients:
                try:
                    admin_html = render_template('email/schedule_admin_notification.html', request=schedule_request)
                    
                    # Send to each recipient
                    for recipient_email in notification_recipients:
                        try:
                            admin_msg = MIMEMultipart('alternative')
                            admin_msg['Subject'] = f"🔔 New Consultation Request - {schedule_request.full_name}"
                            admin_msg['From'] = f"Metabolomics Platform <{mail_sender}>"
                            admin_msg['To'] = recipient_email
                            admin_msg.attach(MIMEText(admin_html, 'html', 'utf-8'))
                            
                            server.send_message(admin_msg)
                            logging.info(f"✅ Notification sent to {recipient_email}")
                        except Exception as e:
                            logging.error(f"❌ Failed to send to {recipient_email}: {e}")
                    
                    results['admin_sent'] = True
                    logging.info(f"✅ Admin notifications sent to {len(notification_recipients)} recipients")
                except Exception as e:
                    logging.error(f"❌ Admin email failed: {e}")
            
            # 2. Send user confirmation
            try:
                user_html = render_template('email/schedule_user_confirmation.html', request=schedule_request)
                user_msg = MIMEMultipart('alternative')
                user_msg['Subject'] = "✅ Consultation Request Confirmed - Metabolomics Platform"
                user_msg['From'] = f"Metabolomics Platform <{mail_sender}>"
                user_msg['To'] = schedule_request.email
                user_msg.attach(MIMEText(user_html, 'html', 'utf-8'))
                
                server.send_message(user_msg)
                results['user_sent'] = True
                logging.info(f"✅ User confirmation sent to {schedule_request.email}")
            except Exception as e:
                logging.error(f"❌ User email failed: {e}")
            
            # NOTE: Removed follow-up email to reduce delays and avoid spam
            # Follow-up can be sent later via a scheduled task if needed
            
        logging.info(f"🎉 Email batch completed: Admin={results['admin_sent']}, User={results['user_sent']}")
        
    except Exception as e:
        logging.error(f"❌ SMTP connection failed: {e}")
    
    return results

def send_password_reset_notification(user, reset_token):
    """
    Send password reset email to user
    
    Args:
        user: User model instance
        reset_token: Password reset token
    
    Returns:
        bool: True if email sent successfully
    """
    return send_email(
        subject="Password Reset Request - Metabolomics Platform",
        recipients=[user.email],
        template='email/password_reset.html',
        context={
            'user': user,
            'reset_token': reset_token,
            'reset_url': f"{current_app.config.get('BASE_URL', '')}/auth/reset-password/{reset_token.token}"
        }
    )

def test_email_configuration():
    """
    Test the email configuration by sending a test email to the admin
    
    Returns:
        bool: True if test email sent successfully
    """
    admin_email = current_app.config.get('MAIL_USERNAME')
    if not admin_email:
        logging.error("No admin email configured for testing")
        return False
    
    return send_email(
        subject="Email Configuration Test - Metabolomics Platform",
        recipients=[admin_email],
        template='email/test_email.html',
        context={
            'test_time': logging.getLogger().handlers[0].formatter.formatTime(logging.LogRecord('test', 0, '', 0, '', (), None))
        }
    )