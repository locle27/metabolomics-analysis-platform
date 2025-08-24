#!/usr/bin/env python3
"""
Authentication Debug Script
Helps diagnose authentication and session issues
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_authentication():
    """Debug authentication setup and current state"""
    try:
        print("🔍 AUTHENTICATION DEBUG REPORT")
        print("=" * 50)
        
        # Import app components
        from app import app
        
        with app.app_context():
            # Check Flask-Login setup
            try:
                from flask_login import current_user
                print("✅ Flask-Login available")
            except ImportError:
                print("❌ Flask-Login not available")
            
            # Check models availability
            try:
                from models import User, db
                print("✅ User model available")
                print("✅ Database model available")
                
                # Test database connection
                try:
                    user_count = User.query.count()
                    print(f"✅ Database connection working - {user_count} users found")
                    
                    if user_count > 0:
                        print("\n👥 Current Users in Database:")
                        users = User.query.all()
                        for user in users:
                            print(f"   - {user.email} ({user.role}) - Active: {user.is_active}")
                    else:
                        print("⚠️  No users in database - run 'python init_database.py'")
                        
                except Exception as db_error:
                    print(f"❌ Database query failed: {db_error}")
                    print("💡 Try running: python init_database.py")
                    
            except Exception as model_error:
                print(f"❌ Model import failed: {model_error}")
            
            # Check session configuration
            print(f"\n🔐 Session Configuration:")
            print(f"   SECRET_KEY configured: {'✅' if app.config.get('SECRET_KEY') else '❌'}")
            print(f"   SESSION_TYPE: {app.config.get('SESSION_TYPE', 'filesystem (default)')}")
            
            # Check available routes related to authentication
            print(f"\n🛣️  Authentication Routes:")
            auth_routes = []
            for rule in app.url_map.iter_rules():
                if any(keyword in rule.endpoint.lower() for keyword in ['login', 'auth', 'user', 'manage']):
                    auth_routes.append(f"   {rule.endpoint}: {rule.rule}")
            
            for route in sorted(auth_routes):
                print(route)
                
            print(f"\n🎯 Quick Test Commands:")
            print(f"   1. Initialize database: python init_database.py")
            print(f"   2. Run application: python app.py")
            print(f"   3. Test login: http://localhost:5000/login")
            print(f"   4. Demo login: admin@demo.com / admin123")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_authentication()