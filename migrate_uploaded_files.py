#!/usr/bin/env python3
"""
Migration script to create uploaded_files table for storing calculator Excel files
"""

import os
import sys
from datetime import datetime
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def create_uploaded_files_table():
    """Create the uploaded_files table for storing Excel files"""
    
    print("Creating uploaded_files table...")
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS uploaded_files (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        calculator_statistics_id INTEGER REFERENCES calculator_statistics(id),
        filename VARCHAR(255) NOT NULL,
        file_content BYTEA NOT NULL,
        file_size INTEGER NOT NULL,
        mime_type VARCHAR(100) DEFAULT 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        file_metadata JSONB,
        CONSTRAINT valid_file_size CHECK (file_size > 0)
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_uploaded_files_user_id ON uploaded_files(user_id);
    CREATE INDEX IF NOT EXISTS idx_uploaded_files_calculator_stats ON uploaded_files(calculator_statistics_id);
    CREATE INDEX IF NOT EXISTS idx_uploaded_files_uploaded_at ON uploaded_files(uploaded_at);
    CREATE INDEX IF NOT EXISTS idx_uploaded_files_filename ON uploaded_files(filename);
    
    -- Add comment to table
    COMMENT ON TABLE uploaded_files IS 'Stores Excel files uploaded for metabolomics calculations';
    COMMENT ON COLUMN uploaded_files.file_content IS 'Binary content of the uploaded Excel file';
    COMMENT ON COLUMN uploaded_files.file_metadata IS 'Additional metadata like sheet names, row count, etc.';
    """
    
    try:
        with app.app_context():
            # Execute the SQL
            with db.engine.begin() as connection:
                connection.execute(text(create_table_sql))
                
            # Verify table was created
            verify_sql = """
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'uploaded_files' 
            AND table_schema = 'public'
            """
            
            with db.engine.begin() as connection:
                result = connection.execute(text(verify_sql))
                count = result.scalar()
                
            if count > 0:
                print("✅ uploaded_files table created successfully!")
                
                # Show table structure
                structure_sql = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = 'uploaded_files'
                ORDER BY ordinal_position;
                """
                
                with db.engine.begin() as connection:
                    result = connection.execute(text(structure_sql))
                    columns = result.fetchall()
                    
                print("\nTable structure:")
                print("-" * 60)
                for col in columns:
                    print(f"{col[0]:<25} {col[1]:<20} {col[2]:<10} {col[3] or ''}")
            else:
                print("❌ Failed to create uploaded_files table")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        return False

def add_weekly_stats_view():
    """Create a materialized view for weekly statistics"""
    
    print("\nCreating weekly statistics view...")
    
    view_sql = """
    CREATE OR REPLACE VIEW weekly_calculator_stats AS
    WITH date_series AS (
        SELECT generate_series(
            CURRENT_DATE - INTERVAL '6 days',
            CURRENT_DATE,
            '1 day'::interval
        )::date as stat_date
    )
    SELECT 
        ds.stat_date,
        COALESCE(u.username, 'Unknown') as username,
        COALESCE(u.id, 0) as user_id,
        COALESCE(COUNT(cs.id), 0) as files_processed,
        COALESCE(SUM(cs.substance_count), 0) as total_substances
    FROM date_series ds
    LEFT JOIN calculator_statistics cs 
        ON DATE(cs.processed_at AT TIME ZONE 'Asia/Ho_Chi_Minh') = ds.stat_date
    LEFT JOIN users u ON cs.user_id = u.id
    GROUP BY ds.stat_date, u.username, u.id
    ORDER BY ds.stat_date DESC, total_substances DESC;
    
    COMMENT ON VIEW weekly_calculator_stats IS 'Weekly aggregated statistics for calculator usage';
    """
    
    try:
        with app.app_context():
            with db.engine.begin() as connection:
                connection.execute(text(view_sql))
                
            print("✅ Weekly statistics view created successfully!")
            
            # Test the view
            test_sql = "SELECT COUNT(*) FROM weekly_calculator_stats"
            with db.engine.begin() as connection:
                result = connection.execute(text(test_sql))
                count = result.scalar()
                print(f"   View contains {count} rows")
                
        return True
        
    except Exception as e:
        print(f"❌ Error creating view: {str(e)}")
        return False

def main():
    """Run all migrations"""
    print("Starting metabolomics calculator file storage migration...")
    print("=" * 60)
    
    # Create uploaded files table
    if not create_uploaded_files_table():
        print("\nMigration failed!")
        return 1
        
    # Create weekly stats view
    if not add_weekly_stats_view():
        print("\nWarning: Weekly stats view creation failed, but table was created successfully")
        
    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("\nNew features added:")
    print("- uploaded_files table for storing Excel files in database")
    print("- weekly_calculator_stats view for aggregated statistics")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())