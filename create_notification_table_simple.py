#!/usr/bin/env python3
"""
Simple notification table creation with proper transaction handling
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("ℹ️ python-dotenv not available, using system environment variables")

def create_notification_table_direct():
    """Create notification_settings table directly with raw SQL"""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    try:
        # Parse the database URL
        url = urlparse(database_url)
        
        # Connect directly to PostgreSQL
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],  # Remove leading slash
            user=url.username,
            password=url.password
        )
        
        print(f"✅ Connected to PostgreSQL database")
        
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'notification_settings'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ notification_settings table already exists")
            cursor.close()
            conn.close()
            return True
        
        # Create the table
        create_table_sql = """
        CREATE TABLE notification_settings (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            enabled BOOLEAN DEFAULT TRUE NOT NULL,
            setting_type VARCHAR(50) DEFAULT 'schedule_consultation' NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_notification_settings_email ON notification_settings(email);
        """
        
        print("🔧 Creating notification_settings table...")
        cursor.execute(create_table_sql)
        conn.commit()
        
        # Verify table creation
        cursor.execute("SELECT COUNT(*) FROM notification_settings;")
        count = cursor.fetchone()[0]
        
        print(f"✅ notification_settings table created successfully! Initial count: {count}")
        
        # Add initial setting for super admin
        cursor.execute("""
            INSERT INTO notification_settings (email, enabled, setting_type) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (email) DO NOTHING;
        """, ('loc22100302@gmail.com', True, 'schedule_consultation'))
        
        conn.commit()
        print(f"✅ Added notification setting for super admin")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating notification table: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

if __name__ == '__main__':
    print("📧 Creating notification_settings table (Direct PostgreSQL)")
    print("=" * 60)
    
    if create_notification_table_direct():
        print("\n✅ SUCCESS: notification_settings table is ready!")
        print("📧 Email notifications will now persist across deployments")
    else:
        print("\n❌ FAILED: Could not create notification_settings table")
        sys.exit(1)