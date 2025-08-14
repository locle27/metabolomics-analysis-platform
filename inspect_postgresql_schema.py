"""
Quick script to inspect existing PostgreSQL schema
"""
import os
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

load_dotenv()

# Get database URL
database_url = os.getenv('DATABASE_URL')
if not database_url:
    database_url = 'postgresql://username:password@localhost/metabolomics_db'

try:
    engine = create_engine(database_url)
    inspector = inspect(engine)
    
    print("🔍 INSPECTING POSTGRESQL SCHEMA")
    print("=" * 50)
    
    # Get all table names
    tables = inspector.get_table_names()
    print(f"📊 Tables found: {tables}")
    print()
    
    # Inspect each table
    for table_name in tables:
        if table_name in ['lipid_classes', 'main_lipids', 'annotated_ions']:
            print(f"📋 Table: {table_name}")
            columns = inspector.get_columns(table_name)
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
            print()
    
    # Test basic connectivity
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM main_lipids WHERE extraction_success = true"))
        count = result.scalar()
        print(f"✅ Database connection successful")
        print(f"📈 Total successful lipids: {count}")
        
        # Check a few lipid names
        result = conn.execute(text("SELECT lipid_name FROM main_lipids LIMIT 3"))
        samples = result.fetchall()
        print(f"📝 Sample lipids: {[row[0] for row in samples]}")

except Exception as e:
    print(f"❌ Database inspection failed: {e}")
    print("💡 Make sure your DATABASE_URL is set correctly")