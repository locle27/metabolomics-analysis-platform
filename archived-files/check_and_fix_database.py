#!/usr/bin/env python3
"""
Database Schema Checker and Fixer
Ensures the User table exists with all required columns for password functionality
"""

import os
from sqlalchemy import create_engine, text, inspect
from models import db, User, VerificationToken

def check_database_connection():
    """Test database connection"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False
            
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_user_table_schema():
    """Check if User table exists and has all required columns"""
    try:
        database_url = os.getenv('DATABASE_URL')
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        # Check if users table exists
        if 'users' not in inspector.get_table_names():
            print("❌ Users table does not exist")
            return False
        
        # Get current columns
        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]
        
        # Required columns for password functionality
        required_columns = [
            'id', 'username', 'email', 'full_name', 'password_hash',
            'role', 'is_active', 'is_verified', 'created_at', 'last_login',
            'failed_login_attempts', 'locked_until', 'last_password_change',
            'auth_method'
        ]
        
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"❌ Missing columns in users table: {missing_columns}")
            return False
        else:
            print("✅ Users table has all required columns")
            return True
            
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return False

def create_user_table():
    """Create or update the users table with proper schema"""
    try:
        from flask import Flask
        
        # Create minimal Flask app for database operations
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created/updated successfully")
            
            # Check if tables were created
            engine = db.engine
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"📊 Available tables: {tables}")
            
            if 'users' in tables:
                columns = inspector.get_columns('users')
                print(f"📋 Users table columns: {[col['name'] for col in columns]}")
                return True
            else:
                print("❌ Users table was not created")
                return False
                
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False

def check_user_exists(email):
    """Check if a specific user exists in the database"""
    try:
        from flask import Flask
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            user = User.query.filter_by(email=email).first()
            if user:
                print(f"✅ User {email} exists in database")
                print(f"   - Username: {user.username}")
                print(f"   - Role: {user.role}")
                print(f"   - Has password: {'Yes' if user.password_hash else 'No'}")
                print(f"   - Auth method: {user.auth_method}")
                return True
            else:
                print(f"❌ User {email} not found in database")
                return False
                
    except Exception as e:
        print(f"❌ User check failed: {e}")
        return False

def create_admin_user():
    """Create the main admin user if it doesn't exist"""
    try:
        from flask import Flask
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            admin_email = 'loc22100302@gmail.com'
            user = User.query.filter_by(email=admin_email).first()
            
            if not user:
                # Create admin user
                user = User(
                    username='loc22100302',
                    email=admin_email,
                    full_name='Main Administrator',
                    role='admin',
                    is_active=True,
                    is_verified=True,
                    auth_method='oauth'
                )
                db.session.add(user)
                db.session.commit()
                print(f"✅ Created admin user: {admin_email}")
            else:
                # Update to admin if not already
                if user.role != 'admin':
                    user.role = 'admin'
                    db.session.commit()
                    print(f"✅ Updated {admin_email} to admin role")
                else:
                    print(f"✅ Admin user {admin_email} already exists")
            
            return True
            
    except Exception as e:
        print(f"❌ Admin user creation failed: {e}")
        return False

def main():
    """Main diagnostic and fix function"""
    print("🔍 METABOLOMICS DATABASE DIAGNOSTIC & FIX")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Step 1: Check database connection
    print("\n1. Testing database connection...")
    if not check_database_connection():
        print("❌ Cannot proceed without database connection")
        return
    
    # Step 2: Check User table schema
    print("\n2. Checking User table schema...")
    if not check_user_table_schema():
        print("\n3. Creating/fixing User table...")
        if not create_user_table():
            print("❌ Failed to create User table")
            return
    
    # Step 3: Check specific admin user
    print("\n4. Checking admin user...")
    admin_email = 'loc22100302@gmail.com'
    if not check_user_exists(admin_email):
        print("\n5. Creating admin user...")
        create_admin_user()
    
    print("\n✅ DATABASE DIAGNOSTIC COMPLETE")
    print("🚀 Password functionality should now work!")

if __name__ == "__main__":
    main()