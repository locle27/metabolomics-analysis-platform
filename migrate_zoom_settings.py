#!/usr/bin/env python3
"""
Migration script to create ChartZoomSettings table in PostgreSQL database
"""

import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:VmyAveAhkGVOFlSiVBWgyIEAUbKAXEPi@mainline.proxy.rlwy.net:36647/lipid-data')

def create_zoom_settings_table():
    """Create the chart_zoom_settings table if it doesn't exist"""
    
    engine = create_engine(DATABASE_URL)
    
    # SQL to create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS chart_zoom_settings (
        id SERIAL PRIMARY KEY,
        lipid_id INTEGER NOT NULL REFERENCES main_lipids(lipid_id),
        chart_type VARCHAR(20) NOT NULL,
        zoom_start FLOAT NOT NULL,
        zoom_end FLOAT NOT NULL,
        is_admin_default BOOLEAN DEFAULT FALSE NOT NULL,
        created_by INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_lipid_chart_zoom UNIQUE(lipid_id, chart_type)
    );
    """
    
    # SQL to create updated_at trigger
    create_trigger_sql = """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    DROP TRIGGER IF EXISTS update_chart_zoom_settings_updated_at ON chart_zoom_settings;
    
    CREATE TRIGGER update_chart_zoom_settings_updated_at 
    BEFORE UPDATE ON chart_zoom_settings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
    """
    
    try:
        with engine.connect() as conn:
            # Create table
            conn.execute(text(create_table_sql))
            print("✅ Created chart_zoom_settings table")
            
            # Create trigger for updated_at
            conn.execute(text(create_trigger_sql))
            print("✅ Created updated_at trigger")
            
            # Check if table was created successfully
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'chart_zoom_settings'
            """))
            count = result.scalar()
            
            if count > 0:
                print("✅ Table chart_zoom_settings verified successfully")
                
                # Get column information
                columns = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'chart_zoom_settings'
                    ORDER BY ordinal_position
                """))
                
                print("\n📊 Table structure:")
                for col in columns:
                    print(f"  - {col.column_name}: {col.data_type} (nullable: {col.is_nullable})")
            else:
                print("❌ Table creation failed")
                
            # Commit the transaction
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False
    
    return True

def migrate_from_local_storage():
    """
    Optional: Migrate any existing zoom settings from browser localStorage
    This would need to be done via the web interface since localStorage is client-side
    """
    print("\n📝 Note: To migrate existing zoom settings from browser localStorage,")
    print("   you'll need to run a one-time migration script in the browser console")
    print("   that reads localStorage and posts the data to the new API endpoint.")

def main():
    print("🚀 Starting ChartZoomSettings migration...")
    print(f"📍 Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
    
    # Create the table
    if create_zoom_settings_table():
        print("\n✅ Migration completed successfully!")
        migrate_from_local_storage()
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()