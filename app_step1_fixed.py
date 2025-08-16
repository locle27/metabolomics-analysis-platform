#!/usr/bin/env python3
"""
Step 1 FIXED: Database + Email working properly
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

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database properly
database_available = False
try:
    from models_postgresql_optimized import db, init_db, create_all_tables, MainLipid, User, ScheduleRequest
    
    # Initialize the database with the app
    init_db(app)
    
    # Create tables if they don't exist
    with app.app_context():
        create_all_tables()
    
    logger.info("✅ Database initialized and tables created successfully")
    database_available = True
    
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    database_available = False

# Initialize email service
email_available = False
try:
    from email_service_simple import send_email, test_email_configuration, get_email_service_status, send_schedule_notification
    logger.info("✅ Email service imported successfully")
    email_available = True
except Exception as e:
    logger.error(f"❌ Email service import failed: {e}")
    email_available = False

@app.route('/')
def homepage():
    """Homepage with system status"""
    # Get database stats if available
    db_stats = "Unable to connect"
    if database_available:
        try:
            with app.app_context():
                lipid_count = MainLipid.query.count()
                user_count = User.query.count()
                schedule_count = ScheduleRequest.query.count()
                db_stats = f"Lipids: {lipid_count}, Users: {user_count}, Requests: {schedule_count}"
        except Exception as e:
            db_stats = f"Connected but query failed: {str(e)}"
    
    # Get email stats if available
    email_stats = "Not available"
    if email_available:
        try:
            status = get_email_service_status()
            email_stats = f"Gmail SMTP: {'✅' if status['gmail_smtp']['available'] else '❌'}"
        except Exception as e:
            email_stats = f"Import failed: {str(e)}"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Metabolomics Platform - Database + Email FIXED</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }}
            h1 {{ color: #2E4C92; }}
            .status {{ background: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .error {{ background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .button {{ background: #2E4C92; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; display: inline-block; }}
            .stats {{ background: #e7f3ff; padding: 10px; border-radius: 5px; margin: 10px 0; font-family: monospace; }}
        </style>
    </head>
    <body>
        <h1>🧬 Metabolomics Platform - Step 1 FIXED</h1>
        
        <div class="{'status' if database_available else 'error'}">
            <h3>🗄️ Database Status: {'✅ Connected & Tables Created' if database_available else '❌ Failed'}</h3>
            <div class="stats">{db_stats}</div>
        </div>
        
        <div class="{'status' if email_available else 'error'}">
            <h3>📧 Email Status: {'✅ Gmail SMTP Ready' if email_available else '❌ Failed'}</h3>
            <div class="stats">{email_stats}</div>
        </div>
        
        <h2>🧪 Test All Features:</h2>
        <div>
            <a href="/test-database-query" class="button">🔍 Database Query</a>
            <a href="/test-email-send" class="button">📧 Send Test Email</a>
            <a href="/schedule-complete" class="button">📅 Full Schedule Test</a>
            <a href="/api/database-view" class="button">📊 Database API</a>
        </div>
        
        <h2>📊 System Status:</h2>
        <ol>
            <li>✅ Flask app running on Railway</li>
            <li>{'✅' if database_available else '❌'} PostgreSQL connection & table creation</li>
            <li>{'✅' if email_available else '❌'} Gmail SMTP service</li>
            <li>🔄 Authentication (next step)</li>
            <li>🔄 Full platform features</li>
        </ol>
        
        <h3>🎯 Ready for Authentication!</h3>
        <p>Once this shows all green, we'll add the authentication layer step by step.</p>
    </body>
    </html>
    """

@app.route('/test-database-query')
def test_database_query():
    """Test comprehensive database queries"""
    if not database_available:
        return jsonify({'status': 'error', 'message': 'Database not available'})
    
    try:
        with app.app_context():
            # Test multiple table queries
            stats = {
                'lipids': MainLipid.query.count(),
                'users': User.query.count(),
                'schedule_requests': ScheduleRequest.query.count()
            }
            
            # Test a more complex query
            if stats['lipids'] > 0:
                sample_lipid = MainLipid.query.first()
                sample_data = {
                    'sample_lipid': sample_lipid.lipid_name if sample_lipid else None,
                    'sample_retention_time': sample_lipid.retention_time if sample_lipid else None
                }
            else:
                sample_data = {'note': 'No lipids found in database'}
            
            return jsonify({
                'status': 'success',
                'message': 'All database queries successful',
                'statistics': stats,
                'sample_data': sample_data,
                'database_url': os.getenv('DATABASE_URL', 'Not set')[:50] + '...'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database query failed: {str(e)}',
            'error_type': type(e).__name__
        })

@app.route('/test-email-send')
def test_email_send():
    """Test email sending with detailed results"""
    if not email_available:
        return jsonify({'status': 'error', 'message': 'Email service not available'})
    
    try:
        result = test_email_configuration()
        
        # Add email service status
        email_status = get_email_service_status()
        result['email_service_status'] = email_status
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Email test failed: {str(e)}',
            'error_type': type(e).__name__
        })

@app.route('/schedule-complete', methods=['GET', 'POST'])
def schedule_complete():
    """Complete scheduling test: Database + Email"""
    if request.method == 'POST':
        if not database_available:
            return jsonify({'status': 'error', 'message': 'Database not available'})
        
        try:
            with app.app_context():
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
                    specific_goals=request.form.get('goals', ''),
                    status='pending'
                )
                
                db.session.add(schedule_request)
                db.session.commit()
                
                db_status = f"✅ Saved to database with ID #{schedule_request.id}"
                
                # Try to send email if available
                email_status = "❌ Email service not available"
                if email_available:
                    try:
                        email_result = send_schedule_notification(schedule_request)
                        admin_status = "✅ Sent" if email_result['admin_sent'] else "❌ Failed"
                        user_status = "✅ Sent" if email_result['user_sent'] else "❌ Failed"
                        email_status = f"Admin: {admin_status}, User: {user_status}"
                        
                        # Add detailed email results
                        email_details = email_result['details']
                        
                    except Exception as e:
                        email_status = f"❌ Email failed: {str(e)}"
                        email_details = {'error': str(e)}
                else:
                    email_details = {'error': 'Email service not available'}
                
                return f"""
                <h1>🎉 Complete Schedule Test Results</h1>
                <div style="font-family: Arial; max-width: 600px; margin: 20px auto; padding: 20px;">
                    <h3>📊 Test Results:</h3>
                    <p><strong>Database:</strong> {db_status}</p>
                    <p><strong>Email:</strong> {email_status}</p>
                    
                    <h3>📋 Submitted Data:</h3>
                    <ul>
                        <li><strong>Name:</strong> {request.form.get('name')}</li>
                        <li><strong>Email:</strong> {request.form.get('email')}</li>
                        <li><strong>Phone:</strong> {request.form.get('phone', 'Not provided')}</li>
                        <li><strong>Organization:</strong> {request.form.get('organization', 'Not provided')}</li>
                        <li><strong>Message:</strong> {request.form.get('message', 'Not provided')}</li>
                    </ul>
                    
                    <p><a href="/" style="background:#2E4C92;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">← Back to Home</a></p>
                </div>
                """
                
        except Exception as e:
            return f"""
            <h1>❌ Schedule Test Failed</h1>
            <div style="font-family: Arial; max-width: 600px; margin: 20px auto; padding: 20px;">
                <p><strong>Error:</strong> {str(e)}</p>
                <p><strong>Error Type:</strong> {type(e).__name__}</p>
                <p><a href="/" style="background:#2E4C92;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">← Back to Home</a></p>
            </div>
            """
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Complete Schedule Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            input, textarea { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; }
            button { background: #2E4C92; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>📅 Complete Schedule Test</h1>
        <p>This will test both database storage AND email notifications.</p>
        
        <form method="POST">
            <p><input type="text" name="name" placeholder="Your Full Name" required></p>
            <p><input type="email" name="email" placeholder="Your Email Address" required></p>
            <p><input type="tel" name="phone" placeholder="Phone Number (optional)"></p>
            <p><input type="text" name="organization" placeholder="Organization/University (optional)"></p>
            <p><textarea name="message" placeholder="Describe your research or consultation needs" rows="4"></textarea></p>
            <p><textarea name="goals" placeholder="Specific goals or objectives (optional)" rows="3"></textarea></p>
            <p><button type="submit">🚀 Test Complete System</button></p>
        </form>
        
        <p><a href="/">← Back to Home</a></p>
    </body>
    </html>
    """

@app.route('/api/database-view')
def api_database_view():
    """Comprehensive database status API"""
    if not database_available:
        return jsonify({'status': 'error', 'message': 'Database not available'})
    
    try:
        with app.app_context():
            stats = {
                'lipids': MainLipid.query.count(),
                'users': User.query.count(),
                'schedule_requests': ScheduleRequest.query.count()
            }
            
            # Get recent schedule requests
            recent_requests = []
            try:
                recent = ScheduleRequest.query.order_by(ScheduleRequest.created_at.desc()).limit(5).all()
                recent_requests = [
                    {
                        'id': req.id,
                        'name': req.full_name,
                        'email': req.email,
                        'status': req.status,
                        'created_at': req.created_at.isoformat() if req.created_at else None
                    }
                    for req in recent
                ]
            except Exception as e:
                recent_requests = [{'error': str(e)}]
            
            return jsonify({
                'status': 'success',
                'database': 'PostgreSQL',
                'statistics': stats,
                'recent_schedule_requests': recent_requests,
                'database_url': os.getenv('DATABASE_URL', 'Not set')[:50] + '...'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error_type': type(e).__name__
        })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'metabolomics-platform-step1-fixed',
        'database': database_available,
        'email': email_available,
        'environment': os.getenv('FLASK_ENV', 'development'),
        'ready_for_auth': database_available and email_available
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)