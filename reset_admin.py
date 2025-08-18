#!/usr/bin/env python3
"""
Reset Admin Account Script
Creates or resets admin account to username: admin, password: admin
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment loaded")
except ImportError:
    print("⚠️ python-dotenv not available")

from models_postgresql_optimized import db, User
from flask import Flask

def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        sys.exit(1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database with app
    db.init_app(app)
    
    return app

def reset_admin_account():
    """Create or reset admin account"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Resetting admin account...")
        
        try:
            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            
            if admin_user:
                print(f"📝 Found existing admin user: {admin_user.email}")
                # Update existing admin
                admin_user.set_password('admin')
                admin_user.role = 'admin'
                admin_user.is_active = True
                admin_user.is_verified = True
                admin_user.auth_method = 'password'
                admin_user.failed_login_attempts = 0
                admin_user.locked_until = None
                admin_user.last_login = None
                
                print("✅ Updated existing admin user")
            else:
                # Create new admin user
                admin_user = User(
                    username='admin',
                    email='admin@metabolomics.local',
                    full_name='System Administrator',
                    role='admin',
                    is_active=True,
                    is_verified=True,
                    auth_method='password',
                    created_at=datetime.utcnow()
                )
                admin_user.set_password('admin')
                
                db.session.add(admin_user)
                print("✅ Created new admin user")
            
            # Save changes
            db.session.commit()
            
            print("🎉 Admin account reset successful!")
            print("📋 Login credentials:")
            print("   Username: admin")
            print("   Password: admin")
            print("   Email: admin@metabolomics.local")
            
            # Verify the account works
            test_user = User.query.filter_by(username='admin').first()
            if test_user and test_user.check_password('admin'):
                print("✅ Password verification successful")
            else:
                print("❌ Password verification failed")
            
        except Exception as e:
            print(f"❌ Error resetting admin account: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    print("🛡️ ADMIN ACCOUNT RESET SCRIPT")
    print("=" * 40)
    
    reset_admin_account()
    
    print("\n🏁 Script completed successfully!")