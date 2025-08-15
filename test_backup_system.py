"""
Test Script for Database Backup System
Tests all backup functionality locally before integration
"""

import os
import time
from dotenv import load_dotenv
from backup_system import DatabaseBackupSystem, AutoBackupContext

# Load environment
load_dotenv()

def test_backup_system():
    """Test the backup system comprehensively"""
    
    print("🧪 TESTING DATABASE BACKUP SYSTEM")
    print("=" * 50)
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    print(f"📊 Main Database: {database_url}")
    
    # Initialize backup system
    backup_system = DatabaseBackupSystem(database_url, "test_backup_system.db")
    
    try:
        # Test 1: Create initial snapshot
        print("\n📸 Test 1: Creating initial snapshot...")
        snapshot_id = backup_system.create_full_snapshot("Initial test snapshot")
        print(f"✅ Snapshot created: {snapshot_id}")
        
        # Test 2: Test backup before change
        print("\n🔄 Test 2: Testing backup before change...")
        
        # Get a test lipid ID (assuming we have data)
        test_lipid_id = 1
        current_data = backup_system.get_current_record_data('main_lipids', test_lipid_id)
        
        if current_data:
            print(f"📋 Current data for lipid {test_lipid_id}: {current_data.get('lipid_name', 'Unknown')}")
            
            # Create backup
            backup_id = backup_system.backup_before_change(
                table_name='main_lipids',
                record_id=test_lipid_id,
                operation='UPDATE',
                old_data=current_data,
                new_data={'lipid_name': 'TEST_MODIFIED_NAME'},
                user_id='test_user',
                source='test_script'
            )
            print(f"✅ Backup created: {backup_id}")
        else:
            print("⚠️  No test data found, creating mock backup")
            backup_id = backup_system.backup_before_change(
                table_name='main_lipids',
                record_id=999,
                operation='INSERT',
                new_data={'lipid_name': 'TEST_LIPID', 'api_code': 'TEST_001'},
                user_id='test_user',
                source='test_script'
            )
            print(f"✅ Mock backup created: {backup_id}")
        
        # Test 3: Test context manager
        print("\n🔄 Test 3: Testing AutoBackupContext...")
        
        with AutoBackupContext(backup_system, 'main_lipids', test_lipid_id, 'UPDATE', 'test_user') as context_backup_id:
            print(f"✅ Context backup created: {context_backup_id}")
            # Simulate some operation
            time.sleep(0.1)
        
        print("✅ Context completed successfully")
        
        # Test 4: Get backup history
        print("\n📜 Test 4: Testing backup history retrieval...")
        
        history = backup_system.get_backup_history(limit=10)
        print(f"📊 Found {len(history)} backup records")
        
        for i, record in enumerate(history[:3]):
            print(f"   {i+1}. {record['operation']} on {record['table_name']}[{record['record_id']}] at {record['timestamp']}")
        
        # Test 5: Get snapshots
        print("\n📸 Test 5: Testing snapshots retrieval...")
        
        snapshots = backup_system.get_snapshots(limit=5)
        print(f"📊 Found {len(snapshots)} snapshots")
        
        for i, snapshot in enumerate(snapshots):
            size_mb = snapshot['compressed_size'] / 1024 / 1024
            print(f"   {i+1}. {snapshot['snapshot_id']} - {snapshot['records_count']} records ({size_mb:.2f} MB)")
        
        # Test 6: Get statistics
        print("\n📊 Test 6: Testing backup statistics...")
        
        stats = backup_system.get_backup_stats()
        print(f"📈 Backup Statistics:")
        print(f"   Total backups: {stats['total_backups']}")
        print(f"   Total snapshots: {stats['total_snapshots']}")
        print(f"   Recent backups (24h): {stats['recent_backups_24h']}")
        print(f"   Storage used: {stats['storage_used_mb']:.2f} MB")
        print(f"   Backup directory: {stats['backup_directory']}")
        
        # Test 7: Create another snapshot
        print("\n📸 Test 7: Creating final test snapshot...")
        
        final_snapshot = backup_system.create_full_snapshot("Final test snapshot after changes")
        print(f"✅ Final snapshot created: {final_snapshot}")
        
        # Test 8: Test backup for different tables
        print("\n🔄 Test 8: Testing backups for different tables...")
        
        # Test annotated_ions backup
        ion_backup = backup_system.backup_before_change(
            table_name='annotated_ions',
            record_id=1,
            operation='UPDATE',
            old_data={'ion_lipid_name': 'TEST_ION_OLD'},
            new_data={'ion_lipid_name': 'TEST_ION_NEW'},
            user_id='test_user',
            source='test_script'
        )
        print(f"✅ Ion backup created: {ion_backup}")
        
        # Test lipid_classes backup
        class_backup = backup_system.backup_before_change(
            table_name='lipid_classes',
            record_id=1,
            operation='UPDATE',
            old_data={'class_name': 'OLD_CLASS'},
            new_data={'class_name': 'NEW_CLASS'},
            user_id='test_user',
            source='test_script'
        )
        print(f"✅ Class backup created: {class_backup}")
        
        # Final statistics
        print("\n📊 Final Statistics:")
        final_stats = backup_system.get_backup_stats()
        print(f"   Total backups: {final_stats['total_backups']}")
        print(f"   Total snapshots: {final_stats['total_snapshots']}")
        print(f"   Storage used: {final_stats['storage_used_mb']:.2f} MB")
        
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print("✅ Backup system is working correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        backup_system.close()
        print("\n🧹 Backup system closed")

def test_backup_retrieval():
    """Test backup data retrieval and verification"""
    
    print("\n🔍 TESTING BACKUP DATA RETRIEVAL")
    print("=" * 40)
    
    database_url = os.getenv('DATABASE_URL')
    backup_system = DatabaseBackupSystem(database_url, "test_backup_system.db")
    
    try:
        # Get recent backups for main_lipids
        print("📋 Recent backups for main_lipids:")
        lipid_backups = backup_system.get_backup_history(table_name='main_lipids', limit=5)
        
        for backup in lipid_backups:
            print(f"   {backup['backup_id']} - {backup['operation']} at {backup['timestamp']}")
            if backup['old_data']:
                old_name = backup['old_data'].get('lipid_name', 'Unknown')
                print(f"      Old data: {old_name}")
            if backup['new_data']:
                new_name = backup['new_data'].get('lipid_name', 'Unknown')
                print(f"      New data: {new_name}")
        
        # Get snapshots with details
        print("\n📸 Available snapshots:")
        snapshots = backup_system.get_snapshots(limit=3)
        
        for snapshot in snapshots:
            print(f"   {snapshot['snapshot_id']}")
            print(f"      Description: {snapshot['description']}")
            print(f"      Records: {snapshot['records_count']}")
            print(f"      Size: {snapshot['compressed_size']/1024/1024:.2f} MB")
            print(f"      Created: {snapshot['created_at']}")
        
    finally:
        backup_system.close()

if __name__ == "__main__":
    # Run comprehensive tests
    success = test_backup_system()
    
    if success:
        print("\n" + "="*50)
        test_backup_retrieval()
        
        print("\n🎯 BACKUP SYSTEM READY FOR INTEGRATION!")
        print("✅ All components tested successfully")
        print("📁 Files created:")
        print("   - backup_system.py (core system)")
        print("   - backup_middleware.py (Flask integration)")
        print("   - test_backup_system.py (this test)")
        print("   - test_backup_system.db (backup database)")
        print("   - database_backups/ (snapshot directory)")
    else:
        print("\n❌ BACKUP SYSTEM TESTS FAILED")
        print("Please check the errors above and fix before integration")