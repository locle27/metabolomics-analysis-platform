#!/usr/bin/env python3
"""
Fix migration script to add missing vietnam_time column to uploaded_files table
This fixes the psycopg2.errors.UndefinedColumn error for vietnam_time
"""

import os
import sys
from datetime import datetime
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def add_vietnam_time_column():
    """Add the missing vietnam_time column to uploaded_files table"""
    
    print("Checking uploaded_files table structure...")
    
    # First, check if the column already exists
    check_column_sql = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'uploaded_files' 
    AND column_name = 'vietnam_time'
    """
    
    try:
        with app.app_context():
            with db.engine.begin() as connection:
                result = connection.execute(text(check_column_sql))
                exists = result.fetchone()
                
            if exists:
                print("✅ vietnam_time column already exists in uploaded_files table")
                return True
                
            print("❌ vietnam_time column is missing. Adding it now...")
            
            # Add the missing vietnam_time column
            alter_table_sql = """
            ALTER TABLE uploaded_files 
            ADD COLUMN vietnam_time VARCHAR(20);
            """
            
            with db.engine.begin() as connection:
                connection.execute(text(alter_table_sql))
                
            print("✅ vietnam_time column added successfully!")
            
            # Update existing records with vietnam_time values
            # Convert existing uploaded_at timestamps to Vietnam time format
            update_existing_sql = """
            UPDATE uploaded_files 
            SET vietnam_time = TO_CHAR(
                (uploaded_at AT TIME ZONE 'UTC') AT TIME ZONE 'Asia/Ho_Chi_Minh', 
                'HH24:MI:SS'
            )
            WHERE vietnam_time IS NULL;
            """
            
            with db.engine.begin() as connection:
                result = connection.execute(text(update_existing_sql))
                updated_count = result.rowcount
                
            print(f"✅ Updated {updated_count} existing records with vietnam_time values")
            
            # Show updated table structure
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
                
            print("\nUpdated table structure:")
            print("-" * 60)
            for col in columns:
                print(f"{col[0]:<25} {col[1]:<20} {col[2]:<10} {col[3] or ''}")
                
            return True
            
    except Exception as e:
        print(f"❌ Error adding vietnam_time column: {str(e)}")
        return False

def verify_fix():
    """Verify that the fix works by testing a query that was failing"""
    
    print("\nTesting the fix with a sample query...")
    
    test_sql = """
    SELECT id, filename, vietnam_time, uploaded_at
    FROM uploaded_files 
    LIMIT 3;
    """
    
    try:
        with app.app_context():
            with db.engine.begin() as connection:
                result = connection.execute(text(test_sql))
                rows = result.fetchall()
                
            if rows:
                print("✅ Query executed successfully! Sample results:")
                print("-" * 50)
                for row in rows:
                    print(f"ID: {row[0]}, File: {row[1]}, VN Time: {row[2]}, Uploaded: {row[3]}")
            else:
                print("✅ Query executed successfully (no data found)")
                
        return True
        
    except Exception as e:
        print(f"❌ Test query failed: {str(e)}")
        return False

def main():
    """Run the vietnam_time column fix"""
    print("Fixing uploaded_files table vietnam_time column issue...")
    print("=" * 60)
    
    # Add the missing column
    if not add_vietnam_time_column():
        print("\nFix failed!")
        return 1
        
    # Test the fix
    if not verify_fix():
        print("\nFix verification failed!")
        return 1
        
    print("\n" + "=" * 60)
    print("Fix completed successfully!")
    print("\nThe vietnam_time column has been added to uploaded_files table.")
    print("The psycopg2.errors.UndefinedColumn error should now be resolved.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())