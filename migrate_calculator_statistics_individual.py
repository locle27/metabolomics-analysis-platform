#!/usr/bin/env python3
"""
Database Migration Script: Update CalculatorStatistics to Track Individual Files
Changes the table from aggregated user statistics to individual file processing records
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

def migrate_calculator_statistics():
    """Update calculator_statistics table structure"""
    
    with app.app_context():
        print("🚀 Starting CalculatorStatistics Migration...")
        
        try:
            # Use transaction for SQLAlchemy 2.0 compatibility
            with db.engine.begin() as connection:
                # First, backup existing data if any
                print("📋 Checking existing data...")
                result = connection.execute(db.text("SELECT COUNT(*) as count FROM calculator_statistics"))
                existing_count = result.fetchone()[0]
                
                if existing_count > 0:
                    print(f"⚠️  Found {existing_count} existing records - backing up...")
                    
                    # Create backup table
                    connection.execute(db.text("""
                        DROP TABLE IF EXISTS calculator_statistics_backup
                    """))
                    
                    connection.execute(db.text("""
                        CREATE TABLE calculator_statistics_backup AS 
                        SELECT * FROM calculator_statistics
                    """))
                    
                    print(f"✅ Backed up {existing_count} records to calculator_statistics_backup")
                
                # Drop the old table
                print("🗑️  Dropping old calculator_statistics table...")
                connection.execute(db.text("DROP TABLE IF EXISTS calculator_statistics"))
                
                # Create new table structure
                print("🏗️  Creating new calculator_statistics table structure...")
                connection.execute(db.text("""
                    CREATE TABLE calculator_statistics (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        filename VARCHAR(255) NOT NULL,
                        substance_count INTEGER NOT NULL,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        vietnam_time VARCHAR(20),
                        CONSTRAINT fk_calculator_stats_user FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                
                # Create indexes for performance
                print("📊 Creating indexes...")
                connection.execute(db.text("CREATE INDEX idx_calculator_stats_user_id ON calculator_statistics(user_id)"))
                connection.execute(db.text("CREATE INDEX idx_calculator_stats_processed_at ON calculator_statistics(processed_at DESC)"))
                
                print("✅ Transaction completed successfully!")
            
            print("✅ Migration completed successfully!")
            print("🎯 New structure:")
            print("   - Each file processing is recorded separately")
            print("   - Vietnam timezone display (UTC+7)")
            print("   - Filename tracking for each upload")
            print("   - Individual substance counts per file")
            
            if existing_count > 0:
                print(f"\n💾 Backup available in 'calculator_statistics_backup' table")
                print("   You can restore old data if needed using SQL queries")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            print("🔄 Transaction automatically rolled back")
            raise e

if __name__ == "__main__":
    print("=" * 60)
    print("CALCULATOR STATISTICS MIGRATION")
    print("Converting from aggregated to individual file tracking")
    print("=" * 60)
    
    migrate_calculator_statistics()
    
    print("\n🎉 Migration completed!")
    print("You can now test the new individual file tracking system.")