#!/usr/bin/env python3
"""
Migration script to create calculator_statistics table for tracking user usage
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Create calculator_statistics table"""
    try:
        # Get database URL from environment
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            print("❌ Error: DATABASE_URL not found in environment variables")
            sys.exit(1)
        
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        print("🚀 Starting migration for calculator_statistics table...")
        
        # Check if table already exists
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'calculator_statistics'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print("⚠️ Table 'calculator_statistics' already exists. Skipping creation.")
                return
        
        # Create the table - use begin() for transaction
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE calculator_statistics (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    upload_count INTEGER DEFAULT 0 NOT NULL,
                    total_substances INTEGER DEFAULT 0 NOT NULL,
                    last_upload_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create index on user_id for faster queries
            conn.execute(text("""
                CREATE INDEX idx_calculator_statistics_user_id 
                ON calculator_statistics(user_id);
            """))
            
            # Create trigger to auto-update updated_at
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """))
            
            conn.execute(text("""
                CREATE TRIGGER update_calculator_statistics_updated_at 
                BEFORE UPDATE ON calculator_statistics 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """))
            
            # Transaction commits automatically with begin()
            
        print("✅ Successfully created calculator_statistics table")
        
        # Verify table structure
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = 'calculator_statistics'
                ORDER BY ordinal_position;
            """))
            
            print("\n📊 Table structure:")
            print("-" * 80)
            print(f"{'Column':<20} {'Type':<20} {'Nullable':<10} {'Default':<30}")
            print("-" * 80)
            
            for row in result:
                print(f"{row[0]:<20} {row[1]:<20} {row[2]:<10} {row[3] or 'NULL':<30}")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_migration()