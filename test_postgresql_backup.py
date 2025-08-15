"""
Test PostgreSQL Backup System
Professional testing suite for backup functionality
"""

import os
import sys
import time
from flask import Flask
from models import db, MainLipid, AnnotatedIon, LipidClass
from backup_system_postgresql import PostgreSQLBackupSystem, auto_backup_context

def create_test_app():
    """Create Flask test application"""
    app = Flask(__name__)
    
    # Use your actual PostgreSQL database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        database_url = "postgresql://postgres:VmyAveAhkGVOFlSiVBWgyIEAUbKAXEPi@mainline.proxy.rlwy.net:36647/lipid-data"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    return app

def test_postgresql_backup_system():
    """Test the PostgreSQL backup system"""
    print("🧪 TESTING POSTGRESQL BACKUP SYSTEM")
    print("=" * 50)
    
    app = create_test_app()
    
    with app.app_context():
        try:
            # Initialize backup system
            backup_system = PostgreSQLBackupSystem(app)
            
            print(f"📊 Main Database: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
            print()
            
            # Test 1: Create initial snapshot
            print("📸 Test 1: Creating initial snapshot...")
            snapshot_id = backup_system.create_full_snapshot("Initial test snapshot")
            print(f"✅ Snapshot created: {snapshot_id}")
            print()
            
            # Test 2: Test backup before change
            print("🔄 Test 2: Testing backup before change...")
            
            # Get a real lipid from database
            test_lipid = db.session.query(MainLipid).first()
            if test_lipid:
                old_data = {
                    'lipid_id': test_lipid.lipid_id,
                    'lipid_name': test_lipid.lipid_name,
                    'lipid_class': test_lipid.lipid_class.class_name if test_lipid.lipid_class else None,
                    'retention_time': float(test_lipid.retention_time) if test_lipid.retention_time else None
                }
                new_data = old_data.copy()
                new_data['lipid_name'] = f"{test_lipid.lipid_name}_TEST_MODIFIED"
                
                backup_id = backup_system.backup_before_change(
                    table_name='main_lipids',
                    record_id=test_lipid.lipid_id,
                    operation='UPDATE',
                    old_data=old_data,
                    new_data=new_data,
                    user_id='test_user',
                    source='test_script'
                )
                print(f"✅ Real data backup created: {backup_id}")
            else:
                print("⚠️ No test data found, creating mock backup")
                backup_id = backup_system.backup_before_change(
                    table_name='main_lipids',
                    record_id=999,
                    operation='INSERT',
                    new_data={'lipid_name': 'TEST_LIPID', 'lipid_class': 'TEST'},
                    user_id='test_user',
                    source='test_script'
                )
                print(f"✅ Mock backup created: {backup_id}")
            print()
            
            # Test 3: Test AutoBackupContext
            print("🔄 Test 3: Testing AutoBackupContext...")
            test_lipid = db.session.query(MainLipid).first()
            if test_lipid:
                old_data = {
                    'lipid_name': test_lipid.lipid_name,
                    'lipid_class': test_lipid.lipid_class.class_name if test_lipid.lipid_class else None
                }
                new_data = {
                    'lipid_name': f"{test_lipid.lipid_name}_CONTEXT_TEST",
                    'lipid_class': test_lipid.lipid_class.class_name if test_lipid.lipid_class else None
                }
                
                with auto_backup_context(
                    backup_system=backup_system,
                    table_name='main_lipids',
                    record_id=test_lipid.lipid_id,
                    operation='UPDATE',
                    old_data=old_data,
                    new_data=new_data,
                    user_id='context_test',
                    source='context_manager'
                ) as context_backup_id:
                    print(f"✅ Context backup created: {context_backup_id}")
                    # Simulate some work (don't actually modify data)
                    time.sleep(0.1)
            print()
            
            # Test 4: Test backup history retrieval
            print("📜 Test 4: Testing backup history retrieval...")
            history = backup_system.get_backup_history(limit=5)
            print(f"📊 Found {len(history)} backup records")
            for i, record in enumerate(history, 1):
                print(f"   {i}. {record.operation} on {record.table_name}[{record.record_id}] at {record.timestamp}")
            print()
            
            # Test 5: Test snapshots retrieval
            print("📸 Test 5: Testing snapshots retrieval...")
            snapshots = backup_system.get_snapshots(limit=3)
            print(f"📊 Found {len(snapshots)} snapshots")
            for i, snapshot in enumerate(snapshots, 1):
                size_mb = snapshot.compressed_size / (1024 * 1024)
                print(f"   {i}. {snapshot.snapshot_id} - {snapshot.records_count} records ({size_mb:.2f} MB)")
            print()
            
            # Test 6: Test backup statistics
            print("📊 Test 6: Testing backup statistics...")
            stats = backup_system.get_backup_statistics()
            print("📈 Backup Statistics:")
            print(f"   Total backups: {stats['total_backups']}")
            print(f"   Total snapshots: {stats['total_snapshots']}")
            print(f"   Recent backups (24h): {stats['recent_backups_24h']}")
            print(f"   Storage used: {stats['storage_used_mb']} MB")
            print(f"   Backup directory: {stats['backup_directory']}")
            print()
            
            # Test 7: Create final test snapshot
            print("📸 Test 7: Creating final test snapshot...")
            final_snapshot = backup_system.create_full_snapshot("Final test snapshot")
            print(f"✅ Final snapshot created: {final_snapshot}")
            print()
            
            # Test 8: Test backups for different tables
            print("🔄 Test 8: Testing backups for different tables...")
            
            # Test annotated_ions backup
            test_ion = db.session.query(AnnotatedIon).first()
            if test_ion:
                ion_backup = backup_system.backup_before_change(
                    table_name='annotated_ions',
                    record_id=test_ion.ion_id,
                    operation='UPDATE',
                    old_data={
                        'ion_lipid_name': test_ion.ion_lipid_name,
                        'main_lipid_id': test_ion.main_lipid_id,
                        'annotation_type': test_ion.annotation_type,
                        'retention_time': float(test_ion.retention_time) if test_ion.retention_time else None
                    },
                    new_data={
                        'ion_lipid_name': f"{test_ion.ion_lipid_name}_UPDATED",
                        'main_lipid_id': test_ion.main_lipid_id,
                        'annotation_type': test_ion.annotation_type,
                        'retention_time': float(test_ion.retention_time) if test_ion.retention_time else None
                    },
                    source='multi_table_test'
                )
                print(f"✅ Ion backup created: {ion_backup}")
            
            # Test lipid_classes backup
            test_class = db.session.query(LipidClass).first()
            if test_class:
                class_backup = backup_system.backup_before_change(
                    table_name='lipid_classes',
                    record_id=test_class.class_id,
                    operation='UPDATE',
                    old_data={
                        'class_name': test_class.class_name,
                        'class_description': test_class.class_description
                    },
                    new_data={
                        'class_name': test_class.class_name,
                        'class_description': f"{test_class.class_description} - Updated" if test_class.class_description else "Updated"
                    },
                    source='multi_table_test'
                )
                print(f"✅ Class backup created: {class_backup}")
            print()
            
            print("✅ ALL POSTGRESQL BACKUP TESTS PASSED!")
            return True
            
        except Exception as e:
            print(f"❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_postgresql_backup_system()
    
    if success:
        print("\n🎉 POSTGRESQL BACKUP SYSTEM READY FOR INTEGRATION")
    else:
        print("\n❌ POSTGRESQL BACKUP SYSTEM TESTS FAILED")
        print("Please check the errors above and fix before integration")
    
    sys.exit(0 if success else 1)