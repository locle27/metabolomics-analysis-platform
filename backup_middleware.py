"""
Flask Middleware for Automatic Database Backup Integration
Automatically triggers backups before any data modification
"""

import functools
import os
from flask import request, session, g
from typing import Dict, Any, Callable
from backup_system import DatabaseBackupSystem, AutoBackupContext

# Global backup system instance
backup_system = None

def init_backup_system(app, main_db_url: str):
    """Initialize backup system with Flask app"""
    global backup_system
    
    backup_db_path = os.path.join(app.instance_path, 'metabolomics_backup_system.db')
    os.makedirs(app.instance_path, exist_ok=True)
    
    backup_system = DatabaseBackupSystem(main_db_url, backup_db_path)
    
    print(f"✅ Backup middleware initialized")
    return backup_system

def get_current_user() -> str:
    """Get current user ID (implement based on your auth system)"""
    # For now, return a default user
    # TODO: Integrate with your authentication system
    return session.get('user_id', 'anonymous')

def get_request_source() -> str:
    """Determine request source"""
    if request.endpoint and 'api' in request.endpoint:
        return 'api'
    elif request.endpoint and 'admin' in request.endpoint:
        return 'admin'
    else:
        return 'web_app'

# Decorator for automatic backup
def auto_backup(table_name: str, operation: str = 'UPDATE'):
    """
    Decorator to automatically backup data before modification
    
    Usage:
    @auto_backup('main_lipids', 'UPDATE')
    def update_lipid(lipid_id, new_data):
        # Your update code here
        pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not backup_system:
                print("⚠️  Backup system not initialized, skipping backup")
                return func(*args, **kwargs)
            
            # Extract record ID from args/kwargs
            record_id = None
            if args and isinstance(args[0], int):
                record_id = args[0]
            elif 'lipid_id' in kwargs:
                record_id = kwargs['lipid_id']
            elif 'ion_id' in kwargs:
                record_id = kwargs['ion_id']
            elif 'class_id' in kwargs:
                record_id = kwargs['class_id']
            
            if record_id is None:
                print("⚠️  Could not determine record ID for backup")
                return func(*args, **kwargs)
            
            # Create backup context
            user_id = get_current_user()
            source = get_request_source()
            
            with AutoBackupContext(backup_system, table_name, record_id, operation, user_id):
                result = func(*args, **kwargs)
                
                # If the function returned new data, update backup with new_data
                if isinstance(result, dict) and operation in ['UPDATE', 'INSERT']:
                    # This could be enhanced to capture the new data
                    pass
                
                return result
        
        return wrapper
    return decorator

# Flask request hooks for automatic backup
def before_request_backup():
    """Before request hook to prepare backup context"""
    g.backup_context = {
        'user_id': get_current_user(),
        'source': get_request_source(),
        'start_time': time.time()
    }

def after_request_backup(response):
    """After request hook to finalize backup operations"""
    if hasattr(g, 'backup_context'):
        # Log request completion if needed
        pass
    return response

# Manual backup functions for complex operations
class BackupManager:
    """High-level backup management functions"""
    
    @staticmethod
    def backup_lipid_update(lipid_id: int, old_data: Dict[str, Any], 
                           new_data: Dict[str, Any]) -> str:
        """Backup before lipid update"""
        if not backup_system:
            return None
        
        return backup_system.backup_before_change(
            table_name='main_lipids',
            record_id=lipid_id,
            operation='UPDATE',
            old_data=old_data,
            new_data=new_data,
            user_id=get_current_user(),
            source=get_request_source()
        )
    
    @staticmethod
    def backup_lipid_delete(lipid_id: int, lipid_data: Dict[str, Any]) -> str:
        """Backup before lipid deletion"""
        if not backup_system:
            return None
        
        return backup_system.backup_before_change(
            table_name='main_lipids',
            record_id=lipid_id,
            operation='DELETE',
            old_data=lipid_data,
            user_id=get_current_user(),
            source=get_request_source()
        )
    
    @staticmethod
    def backup_ion_update(ion_id: int, old_data: Dict[str, Any], 
                         new_data: Dict[str, Any]) -> str:
        """Backup before ion update"""
        if not backup_system:
            return None
        
        return backup_system.backup_before_change(
            table_name='annotated_ions',
            record_id=ion_id,
            operation='UPDATE',
            old_data=old_data,
            new_data=new_data,
            user_id=get_current_user(),
            source=get_request_source()
        )
    
    @staticmethod
    def create_snapshot(description: str = None) -> str:
        """Create full database snapshot"""
        if not backup_system:
            return None
        
        return backup_system.create_full_snapshot(description)
    
    @staticmethod
    def get_backup_history(table_name: str = None, record_id: int = None, 
                          limit: int = 100) -> list:
        """Get backup history"""
        if not backup_system:
            return []
        
        return backup_system.get_backup_history(table_name, record_id, limit)
    
    @staticmethod
    def get_snapshots(limit: int = 20) -> list:
        """Get available snapshots"""
        if not backup_system:
            return []
        
        return backup_system.get_snapshots(limit)
    
    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """Get backup system statistics"""
        if not backup_system:
            return {}
        
        return backup_system.get_backup_stats()
    
    @staticmethod
    def cleanup_old_backups(days: int = 30) -> int:
        """Clean up old backups"""
        if not backup_system:
            return 0
        
        return backup_system.cleanup_old_backups(days)

# Integration helpers for Flask routes
def safe_update_with_backup(update_func: Callable, table_name: str, 
                           record_id: int, new_data: Dict[str, Any]):
    """Safely update data with automatic backup"""
    if not backup_system:
        print("⚠️  No backup system, proceeding without backup")
        return update_func()
    
    # Get current data
    old_data = backup_system.get_current_record_data(table_name, record_id)
    
    # Create backup
    backup_id = backup_system.backup_before_change(
        table_name=table_name,
        record_id=record_id,
        operation='UPDATE',
        old_data=old_data,
        new_data=new_data,
        user_id=get_current_user(),
        source=get_request_source()
    )
    
    try:
        # Perform update
        result = update_func()
        print(f"✅ Update completed with backup {backup_id}")
        return result
        
    except Exception as e:
        print(f"❌ Update failed, backup {backup_id} preserved: {e}")
        raise

def safe_delete_with_backup(delete_func: Callable, table_name: str, 
                           record_id: int):
    """Safely delete data with automatic backup"""
    if not backup_system:
        print("⚠️  No backup system, proceeding without backup")
        return delete_func()
    
    # Get current data before deletion
    old_data = backup_system.get_current_record_data(table_name, record_id)
    
    # Create backup
    backup_id = backup_system.backup_before_change(
        table_name=table_name,
        record_id=record_id,
        operation='DELETE',
        old_data=old_data,
        user_id=get_current_user(),
        source=get_request_source()
    )
    
    try:
        # Perform deletion
        result = delete_func()
        print(f"✅ Deletion completed with backup {backup_id}")
        return result
        
    except Exception as e:
        print(f"❌ Deletion failed, backup {backup_id} preserved: {e}")
        raise