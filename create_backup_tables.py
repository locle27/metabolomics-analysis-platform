"""
Create Backup Tables in PostgreSQL Database
Migration script to add backup functionality to existing database
"""

import os
import sys
from flask import Flask
from models import db, BackupHistory, BackupSnapshots, BackupStats

def create_app():
    """Create Flask application for migration"""
    app = Flask(__name__)
    
    # Use your actual PostgreSQL database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        database_url = "postgresql://postgres:VmyAveAhkGVOFlSiVBWgyIEAUbKAXEPi@mainline.proxy.rlwy.net:36647/lipid-data"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    return app

def create_backup_tables():
    """Create backup tables in PostgreSQL database"""
    print("🚀 CREATING POSTGRESQL BACKUP TABLES")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            print(f"📊 Connecting to: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
            
            # Create all tables (including backup tables)
            print("📋 Creating backup tables...")
            db.create_all()
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            backup_tables = ['backup_history', 'backup_snapshots', 'backup_stats']
            created_tables = []
            
            for table_name in backup_tables:
                if inspector.has_table(table_name):
                    created_tables.append(table_name)
                    print(f"✅ Table '{table_name}' created successfully")
                else:
                    print(f"❌ Table '{table_name}' was not created")
            
            if len(created_tables) == len(backup_tables):
                print(f"\n🎉 ALL BACKUP TABLES CREATED SUCCESSFULLY!")
                print("🔧 Tables created:")
                for table in created_tables:
                    print(f"   - {table}")
                
                # Show table schemas
                print("\n📋 Table Schemas:")
                for table_name in backup_tables:
                    columns = inspector.get_columns(table_name)
                    print(f"\n{table_name}:")
                    for col in columns:
                        print(f"   - {col['name']}: {col['type']}")
                
                return True
            else:
                print(f"\n❌ SOME TABLES FAILED TO CREATE")
                return False
                
        except Exception as e:
            print(f"❌ ERROR CREATING BACKUP TABLES: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = create_backup_tables()
    
    if success:
        print("\n✅ BACKUP TABLES READY!")
        print("🚀 You can now run: python test_postgresql_backup.py")
    else:
        print("\n❌ BACKUP TABLE CREATION FAILED")
    
    sys.exit(0 if success else 1)