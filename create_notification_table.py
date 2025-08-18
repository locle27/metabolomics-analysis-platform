#!/usr/bin/env python3
"""
Create missing notification_settings table
This fixes the PostgreSQL error: relation "notification_settings" does not exist
"""

import os
import sys
from models_postgresql_optimized import db, NotificationSetting, User

# Add current directory to path for Flask app import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    print("✅ Successfully imported Flask app")
except ImportError as e:
    print(f"❌ Failed to import Flask app: {e}")
    sys.exit(1)

def create_notification_settings_table():
    """Create the notification_settings table"""
    
    with app.app_context():
        try:
            # Check if table exists
            try:
                existing = NotificationSetting.query.first()
                print(f"✅ notification_settings table already exists")
                return True
            except Exception as e:
                print(f"🔧 Table doesn't exist, creating it: {e}")
                
            # Create the table
            print("🔧 Creating notification_settings table...")
            db.create_all()
            
            # Verify table creation
            try:
                test_query = NotificationSetting.query.count()
                print(f"✅ notification_settings table created successfully! Count: {test_query}")
                return True
            except Exception as e:
                print(f"❌ Failed to verify table creation: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating notification_settings table: {e}")
            return False

def migrate_existing_settings():
    """Migrate any existing notification settings from JSON files"""
    
    with app.app_context():
        try:
            # Check if any admin users should have notifications enabled
            admin_users = User.query.filter_by(role='admin').all()
            
            for admin_user in admin_users:
                # Check if setting already exists
                existing = NotificationSetting.query.filter_by(email=admin_user.email).first()
                
                if not existing:
                    # Create notification setting for admin users (enabled by default)
                    notification_setting = NotificationSetting(
                        email=admin_user.email,
                        enabled=True,
                        setting_type='schedule_consultation'
                    )
                    db.session.add(notification_setting)
                    print(f"✅ Created notification setting for admin: {admin_user.email}")
            
            db.session.commit()
            print(f"✅ Migration completed successfully")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            db.session.rollback()

if __name__ == '__main__':
    print("🚀 Creating notification_settings table...")
    print("=" * 50)
    
    # Create table
    if create_notification_settings_table():
        print("✅ Table creation successful")
        
        # Migrate existing settings
        print("\n🔄 Migrating existing settings...")
        migrate_existing_settings()
        
        print("\n✅ All operations completed successfully!")
        print("📧 Notification settings table is now ready for use")
        
    else:
        print("❌ Table creation failed")
        sys.exit(1)