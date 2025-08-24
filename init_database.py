#!/usr/bin/env python3
"""
Database Initialization Script for Metabolomics Platform
Creates initial users and sets up the database properly
"""

import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔧 METABOLOMICS DATABASE INITIALIZATION")
print("=" * 50)

try:
    # Import app and models
    from app import app, db, User
    print("✅ App and models imported successfully")
except ImportError as e:
    print(f"❌ Failed to import app/models: {e}")
    sys.exit(1)

def init_database():
    """Initialize database with demo users"""
    try:
        with app.app_context():
            print("🔧 Creating database tables...")
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Check if users already exist
            existing_users = User.query.count()
            print(f"🔍 Found {existing_users} existing users")
            
            if existing_users > 0:
                print("⚠️ Users already exist in database")
                choice = input("Do you want to add more demo users anyway? (y/n): ").lower()
                if choice != 'y':
                    print("🔄 Skipping user creation")
                    return
            
            # Create demo users
            demo_users = [
                {
                    'username': 'admin',
                    'email': 'admin@metabolomics.com',
                    'full_name': 'System Administrator',
                    'role': 'admin',
                    'is_active': True,
                    'is_verified': True,
                    'auth_method': 'demo'
                },
                {
                    'username': 'manager',
                    'email': 'manager@metabolomics.com', 
                    'full_name': 'Research Manager',
                    'role': 'manager',
                    'is_active': True,
                    'is_verified': True,
                    'auth_method': 'demo'
                },
                {
                    'username': 'researcher1',
                    'email': 'researcher1@metabolomics.com',
                    'full_name': 'Senior Researcher',
                    'role': 'user',
                    'is_active': True,
                    'is_verified': True,
                    'auth_method': 'demo'
                },
                {
                    'username': 'researcher2',
                    'email': 'researcher2@metabolomics.com',
                    'full_name': 'Junior Researcher', 
                    'role': 'user',
                    'is_active': True,
                    'is_verified': False,
                    'auth_method': 'demo'
                },
                {
                    'username': 'scientist',
                    'email': 'scientist@metabolomics.com',
                    'full_name': 'Lab Scientist',
                    'role': 'user', 
                    'is_active': True,
                    'is_verified': True,
                    'auth_method': 'demo'
                }
            ]
            
            created_count = 0
            for user_data in demo_users:
                # Check if user already exists
                existing = User.query.filter_by(email=user_data['email']).first()
                if existing:
                    print(f"⚠️ User {user_data['email']} already exists, skipping")
                    continue
                    
                # Create new user
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    full_name=user_data['full_name'],
                    role=user_data['role'],
                    is_active=user_data['is_active'],
                    created_at=datetime.utcnow()
                )
                
                # Add optional fields if User model supports them
                try:
                    if hasattr(user, 'is_verified'):
                        user.is_verified = user_data['is_verified']
                    if hasattr(user, 'auth_method'):
                        user.auth_method = user_data['auth_method'] 
                except:
                    pass
                
                db.session.add(user)
                created_count += 1
                print(f"✅ Created user: {user_data['full_name']} ({user_data['role']})")
            
            # Commit all changes
            db.session.commit()
            print(f"🎉 Successfully created {created_count} demo users!")
            
            # Show final stats
            total_users = User.query.count()
            admin_count = User.query.filter_by(role='admin').count()
            manager_count = User.query.filter_by(role='manager').count() 
            user_count = User.query.filter_by(role='user').count()
            
            print("\n📊 DATABASE SUMMARY:")
            print(f"   Total Users: {total_users}")
            print(f"   Administrators: {admin_count}")
            print(f"   Managers: {manager_count}")
            print(f"   Researchers: {user_count}")
            print("\n🔑 DEMO LOGIN CREDENTIALS:")
            print("   Admin: admin@metabolomics.com")
            print("   Manager: manager@metabolomics.com")
            print("   Researcher: researcher1@metabolomics.com")
            print("\n✅ Database initialization complete!")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

def check_database_status():
    """Check current database status"""
    try:
        with app.app_context():
            user_count = User.query.count()
            print(f"📊 Current database has {user_count} users")
            
            if user_count > 0:
                users = User.query.all()
                print("\n👥 CURRENT USERS:")
                for user in users:
                    status = "✅ Active" if user.is_active else "❌ Inactive"
                    print(f"   {user.full_name or user.username} ({user.email}) - {user.role} - {status}")
            else:
                print("⚠️ No users found in database")
                
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == '__main__':
    print("🚀 Starting database initialization...")
    
    # Check current status first
    try:
        check_database_status()
    except Exception as e:
        print(f"⚠️ Could not check database status: {e}")
    
    print("\n" + "="*50)
    
    # Initialize database
    init_database()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run the Flask app: python app.py")
    print("2. Visit: http://localhost:5000/manage-users")
    print("3. Login with any of the demo accounts above")
    print("4. The manage-users page should now show real users!")