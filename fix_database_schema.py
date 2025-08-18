#!/usr/bin/env python3
"""
Database Schema Fix for Railway PostgreSQL
Adds missing columns to schedule_requests table
"""

import os
import sys
from sqlalchemy import create_engine, text

def fix_database_schema():
    """Add missing columns to schedule_requests table"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        print("🔄 Connecting to Railway PostgreSQL database...")
        
        with engine.connect() as conn:
            # Check current table structure
            print("📋 Checking current schedule_requests table structure...")
            
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'schedule_requests' 
                ORDER BY ordinal_position;
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"📄 Existing columns: {existing_columns}")
            
            # Add missing columns
            columns_to_add = []
            
            if 'contacted_at' not in existing_columns:
                columns_to_add.append(('contacted_at', 'TIMESTAMP'))
                
            if 'notes' not in existing_columns:
                columns_to_add.append(('notes', 'TEXT'))
            
            if not columns_to_add:
                print("✅ All required columns already exist!")
                return True
            
            # Add missing columns
            for column_name, column_type in columns_to_add:
                print(f"➕ Adding column: {column_name} ({column_type})")
                conn.execute(text(f"ALTER TABLE schedule_requests ADD COLUMN IF NOT EXISTS {column_name} {column_type};"))
                conn.commit()
                print(f"✅ Added {column_name} column successfully")
            
            # Verify final structure
            print("\n📋 Final table structure:")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'schedule_requests' 
                ORDER BY ordinal_position;
            """))
            
            for row in result.fetchall():
                print(f"  - {row[0]} ({row[1]}, nullable: {row[2]})")
            
            print("\n✅ Database schema fix completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Database schema fix failed: {e}")
        return False

if __name__ == "__main__":
    # Load environment variables from .env file if running locally
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📁 Loaded .env file")
    except ImportError:
        print("📁 python-dotenv not available, using system environment")
    
    success = fix_database_schema()
    sys.exit(0 if success else 1)