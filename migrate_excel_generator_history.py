#!/usr/bin/env python3
"""
Database Migration Script: Create ExcelGeneratorHistory table
Creates a new table to store Excel generator configuration history online
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path so we can import our app
sys.path.insert(0, str(Path(__file__).parent))

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("ℹ️ python-dotenv not available, using system environment variables")

from app import app
from models import db

def create_excel_generator_history_table():
    """Create excel_generator_history table for storing configuration history online"""
    
    with app.app_context():
        print("🚀 Starting Excel Generator History Migration...")
        
        try:
            # Use transaction for SQLAlchemy 2.0 compatibility
            with db.engine.begin() as connection:
                
                print("🏗️  Creating excel_generator_history table...")
                connection.execute(db.text("""
                    CREATE TABLE IF NOT EXISTS excel_generator_history (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        title VARCHAR(255) NOT NULL,
                        inputs JSON NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        vietnam_time VARCHAR(20),
                        CONSTRAINT fk_excel_history_user FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                
                # Create indexes for performance
                print("📊 Creating indexes...")
                connection.execute(db.text("CREATE INDEX IF NOT EXISTS idx_excel_history_user_id ON excel_generator_history(user_id)"))
                connection.execute(db.text("CREATE INDEX IF NOT EXISTS idx_excel_history_created_at ON excel_generator_history(created_at DESC)"))
                
                print("✅ Transaction completed successfully!")
            
            print("✅ Migration completed successfully!")
            print("🎯 New table structure:")
            print("   - id: Primary key")
            print("   - user_id: Foreign key to users table")
            print("   - title: Configuration name/title")
            print("   - inputs: JSON field with all form inputs")
            print("   - created_at: Timestamp when saved")
            print("   - vietnam_time: Formatted Vietnam time (UTC+7)")
            print("")
            print("🔗 Features:")
            print("   - Stores configuration history online in PostgreSQL")
            print("   - Survives logout/login cycles")
            print("   - User-specific history (multi-user support)")
            print("   - Fast lookup with database indexes")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            print("🔄 Transaction automatically rolled back")
            raise e

if __name__ == "__main__":
    print("=" * 60)
    print("EXCEL GENERATOR HISTORY MIGRATION")
    print("Creating online storage for configuration history")
    print("=" * 60)
    
    create_excel_generator_history_table()
    
    print("\n🎉 Migration completed!")
    print("Users can now save and restore their Excel generator configurations!")