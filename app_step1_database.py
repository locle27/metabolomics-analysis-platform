#!/usr/bin/env python3
"""
Step 1: Add database connectivity
Working email service + database models
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple configuration
BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=BASE_DIR / "templates", static_folder=BASE_DIR / "static")

# Fix for Railway HTTPS proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
app.secret_key = os.getenv('SECRET_KEY', 'metabolomics-dev-key-change-in-production')

# Initialize database
try:
    from models_postgresql_optimized import db, init_db, MainLipid, User, ScheduleRequest
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with the app
    init_db(app)
    
    logger.info("✅ Database initialized successfully")
    database_available = True
    
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    database_available = False

# Initialize email service
try:
    from email_service_simple import send_email, test_email_configuration, get_email_service_status
    logger.info("✅ Email service imported successfully")
    email_available = True
except Exception as e:
    logger.error(f"❌ Email service import failed: {e}")
    email_available = False

@app.route('/')
def homepage():
    """Homepage with system status"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Metabolomics Platform - Step 1</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
            h1 {{ color: #2E4C92; }}
            .status {{ background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .error {{ background: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .button {{ background: #2E4C92; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; display: inline-block; }}
        </style>
    </head>
    <body>
        <h1>🧬 Metabolomics Platform - Step 1</h1>
        
        <div class="{'status' if database_available else 'error'}">
            <h3>🗄️ Database Status: {'✅ Connected' if database_available else '❌ Failed'}</h3>
            <p>PostgreSQL connection and models</p>
        </div>
        
        <div class="{'status' if email_available else 'error'}">
            <h3>📧 Email Status: {'✅ Ready' if email_available else '❌ Failed'}</h3>
            <p>Gmail SMTP service</p>
        </div>
        
        <h2>🧪 Test Features:</h2>
        <div>
            <a href="/test-database-query" class="button">🔍 Test Database Query</a>
            <a href="/test-email-send" class="button">📧 Test Email Send</a>
            <a href="/schedule-simple" class="button">📅 Simple Schedule</a>
            <a href="/api/database-view" class="button">📊 Database API</a>
        </div>
        
        <h2>📊 Progress:</h2>
        <ol>
            <li>✅ Basic Flask app working</li>
            <li>{'✅' if database_available else '🔄'} Database connection</li>
            <li>{'✅' if email_available else '🔄'} Email service</li>
            <li>🔄 Authentication system</li>
            <li>🔄 Full features</li>
        </ol>
    </body>
    </html>
    """

@app.route('/test-database-query')
def test_database_query():
    """Test actual database query"""
    if not database_available:
        return jsonify({'status': 'error', 'message': 'Database not available'})
    
    try:
        # Try to count lipids
        lipid_count = MainLipid.query.count()
        user_count = User.query.count()
        
        return jsonify({
            'status': 'success',
            'message': 'Database query successful',
            'data': {
                'lipids': lipid_count,
                'users': user_count
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database query failed: {str(e)}'
        })

@app.route('/test-email-send')
def test_email_send():
    """Test email sending"""
    if not email_available:
        return jsonify({'status': 'error', 'message': 'Email service not available'})
    
    try:
        result = test_email_configuration()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Email test failed: {str(e)}'
        })

@app.route('/schedule-simple', methods=['GET', 'POST'])
def schedule_simple():
    """Simple scheduling with database storage"""
    if request.method == 'POST':
        if not database_available:
            return jsonify({'status': 'error', 'message': 'Database not available'})
        
        try:
            # Create schedule request
            schedule_request = ScheduleRequest(
                full_name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone', ''),
                organization=request.form.get('organization', ''),
                request_type='consultation',
                priority='medium',
                meeting_type='online',
                research_description=request.form.get('message', ''),
                status='pending'
            )
            
            db.session.add(schedule_request)
            db.session.commit()
            
            # Try to send email if available
            if email_available:
                try:
                    from email_service_simple import send_schedule_notification
                    email_result = send_schedule_notification(schedule_request)
                    email_status = f"Admin: {'✅' if email_result['admin_sent'] else '❌'}, User: {'✅' if email_result['user_sent'] else '❌'}"
                except Exception as e:
                    email_status = f"❌ Email failed: {str(e)}"
            else:
                email_status = "⚠️ Email service not available"
            
            return f"""
            <h1>✅ Schedule Request Submitted</h1>
            <p><strong>Request ID:</strong> #{schedule_request.id}</p>
            <p><strong>Database:</strong> ✅ Saved successfully</p>
            <p><strong>Email:</strong> {email_status}</p>
            <a href="/">← Back to Home</a>
            """
            
        except Exception as e:
            return f"""
            <h1>❌ Schedule Request Failed</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <a href="/">← Back to Home</a>
            """
    
    return """
    <h1>📅 Schedule Consultation (Step 1)</h1>
    <form method="POST">
        <p><input type="text" name="name" placeholder="Your Name" required style="width:300px;padding:8px;"></p>
        <p><input type="email" name="email" placeholder="Your Email" required style="width:300px;padding:8px;"></p>
        <p><input type="tel" name="phone" placeholder="Phone (optional)" style="width:300px;padding:8px;"></p>
        <p><input type="text" name="organization" placeholder="Organization (optional)" style="width:300px;padding:8px;"></p>
        <p><textarea name="message" placeholder="Describe your research or consultation needs" style="width:300px;height:100px;padding:8px;"></textarea></p>
        <p><button type="submit" style="background:#2E4C92;color:white;padding:10px 20px;border:none;border-radius:5px;">Submit Request</button></p>
    </form>
    <a href="/">← Back to Home</a>
    """

@app.route('/api/database-view')
def api_database_view():
    """API to view database status"""
    if not database_available:
        return jsonify({'status': 'error', 'message': 'Database not available'})
    
    try:
        stats = {
            'lipids': MainLipid.query.count(),
            'users': User.query.count(),
            'schedule_requests': ScheduleRequest.query.count()
        }
        
        return jsonify({
            'status': 'success',
            'database': 'PostgreSQL',
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'metabolomics-platform-step1',
        'database': database_available,
        'email': email_available,
        'environment': os.getenv('FLASK_ENV', 'development')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)