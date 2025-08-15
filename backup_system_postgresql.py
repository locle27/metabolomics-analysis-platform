"""
PostgreSQL-based Database Backup System
Professional backup and history tracking for metabolomics platform
"""

import json
import hashlib
import time
import threading
import uuid
import os
import gzip
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from flask import current_app

# Import our PostgreSQL models
try:
    from models_postgresql_optimized import db, BackupHistory, BackupSnapshots, BackupStats, MainLipid, AnnotatedIon, LipidClass
except ImportError:
    from models import db, BackupHistory, BackupSnapshots, BackupStats, MainLipid, AnnotatedIon, LipidClass


@dataclass
class BackupRecord:
    """Data class for backup records"""
    backup_id: str
    table_name: str
    record_id: int
    operation: str
    old_data: Dict[str, Any]
    new_data: Dict[str, Any]
    timestamp: float
    user_id: str
    source: str
    backup_hash: str


class PostgreSQLBackupSystem:
    """
    Professional PostgreSQL-based backup system
    Stores backup data in the same database as main data
    """
    
    def __init__(self, app=None):
        self.app = app
        self.backup_dir = "database_backups"
        self.session = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Create backup tables if they don't exist
        with app.app_context():
            try:
                db.create_all()  # This will create backup tables
                print("✅ PostgreSQL backup tables initialized")
            except Exception as e:
                print(f"❌ Error initializing backup tables: {e}")
    
    def get_session(self):
        """Get database session"""
        if not self.session:
            self.session = db.session
        return self.session
    
    def generate_backup_id(self) -> str:
        """Generate unique backup ID with high entropy"""
        timestamp = str(time.time())
        random_uuid = str(uuid.uuid4())
        thread_id = str(threading.current_thread().ident)
        hash_input = f"{timestamp}_{thread_id}_{random_uuid}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    def serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize data to be JSON-compatible"""
        if not data:
            return {}
        
        serialized = {}
        for key, value in data.items():
            if hasattr(value, '__table__'):  # SQLAlchemy object
                # Convert SQLAlchemy object to dict
                serialized[key] = self._serialize_record(value)
            elif hasattr(value, 'isoformat'):  # datetime object
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        
        return serialized
    
    def calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash for data integrity"""
        if not data:
            return ""
        
        # Serialize data before hashing
        serialized_data = self.serialize_data(data)
        data_str = json.dumps(serialized_data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def backup_before_change(self, table_name: str, record_id: int, 
                           operation: str, old_data: Dict[str, Any] = None, 
                           new_data: Dict[str, Any] = None,
                           user_id: str = None, source: str = "web_app") -> str:
        """
        Create backup record before any data change using PostgreSQL
        """
        session = self.get_session()
        timestamp = time.time()
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                backup_id = self.generate_backup_id()
                
                # Serialize data to ensure JSON compatibility
                serialized_old_data = self.serialize_data(old_data) if old_data else None
                serialized_new_data = self.serialize_data(new_data) if new_data else None
                
                # Create backup record using SQLAlchemy model
                backup_record = BackupHistory(
                    backup_id=backup_id,
                    table_name=table_name,
                    record_id=record_id,
                    operation=operation,
                    old_data=serialized_old_data,
                    new_data=serialized_new_data,
                    timestamp=timestamp,
                    user_id=user_id,
                    source=source,
                    backup_hash=self.calculate_data_hash(old_data or new_data)
                )
                
                # Add to session and commit
                session.add(backup_record)
                session.commit()
                
                print(f"🔄 Backup created: {operation} on {table_name}[{record_id}] -> {backup_id}")
                return backup_id
                
            except IntegrityError as e:
                session.rollback()
                if "backup_history_pkey" in str(e) and attempt < max_retries - 1:
                    print(f"⚠️ Backup ID collision (attempt {attempt + 1}), retrying...")
                    time.sleep(0.001)  # Small delay before retry
                    continue
                else:
                    raise e
            except Exception as e:
                session.rollback()
                print(f"❌ Backup error: {e}")
                raise e
    
    def create_full_snapshot(self, description: str = None) -> str:
        """
        Create full database snapshot
        """
        session = self.get_session()
        timestamp = time.time()
        
        if not description:
            description = f"Full snapshot created at {datetime.fromtimestamp(timestamp)}"
        
        snapshot_id = f"snapshot_{int(timestamp)}"
        
        try:
            # Get counts for all main tables
            lipid_classes_count = session.query(LipidClass).count()
            main_lipids_count = session.query(MainLipid).count()
            annotated_ions_count = session.query(AnnotatedIon).count()
            
            total_records = lipid_classes_count + main_lipids_count + annotated_ions_count
            tables_count = 3
            
            # Export data to compressed file
            export_file = os.path.join(self.backup_dir, f"{snapshot_id}.json.gz")
            
            export_data = {
                'timestamp': timestamp,
                'snapshot_id': snapshot_id,
                'tables': {
                    'lipid_classes': [self._serialize_record(record) for record in session.query(LipidClass).all()],
                    'main_lipids': [self._serialize_record(record) for record in session.query(MainLipid).all()],
                    'annotated_ions': [self._serialize_record(record) for record in session.query(AnnotatedIon).all()]
                }
            }
            
            # Compress and save
            with gzip.open(export_file, 'wt', encoding='utf-8') as f:
                json.dump(export_data, f, default=str, indent=2)
            
            # Get file size
            file_size = os.path.getsize(export_file)
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"📊 Exported lipid_classes: {lipid_classes_count} records")
            print(f"📊 Exported main_lipids: {main_lipids_count} records")
            print(f"📊 Exported annotated_ions: {annotated_ions_count} records")
            
            # Create snapshot record
            snapshot_record = BackupSnapshots(
                snapshot_id=snapshot_id,
                timestamp=timestamp,
                description=description,
                tables_count=tables_count,
                records_count=total_records,
                compressed_size=file_size,
                file_path=export_file,
                backup_hash=self.calculate_data_hash({'records': total_records, 'timestamp': timestamp})
            )
            
            session.add(snapshot_record)
            session.commit()
            
            print(f"📸 Snapshot created: {snapshot_id}")
            print(f"   Records: {total_records}, Size: {file_size_mb:.2f} MB")
            
            return snapshot_id
            
        except Exception as e:
            session.rollback()
            print(f"❌ Snapshot creation failed: {e}")
            raise e
    
    def _serialize_record(self, record) -> Dict[str, Any]:
        """Convert SQLAlchemy record to dictionary"""
        result = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result
    
    def get_backup_history(self, limit: int = 50, table_name: str = None) -> List[BackupHistory]:
        """Get backup history records"""
        session = self.get_session()
        
        query = session.query(BackupHistory).order_by(BackupHistory.timestamp.desc())
        
        if table_name:
            query = query.filter(BackupHistory.table_name == table_name)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_snapshots(self, limit: int = 10) -> List[BackupSnapshots]:
        """Get snapshot records"""
        session = self.get_session()
        
        return session.query(BackupSnapshots).order_by(
            BackupSnapshots.timestamp.desc()
        ).limit(limit).all()
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get comprehensive backup statistics"""
        session = self.get_session()
        
        try:
            # Count total backups
            total_backups = session.query(BackupHistory).count()
            
            # Count total snapshots
            total_snapshots = session.query(BackupSnapshots).count()
            
            # Count recent backups (last 24 hours)
            recent_timestamp = time.time() - (24 * 60 * 60)
            recent_backups = session.query(BackupHistory).filter(
                BackupHistory.timestamp >= recent_timestamp
            ).count()
            
            # Calculate total storage used by snapshots
            total_storage = session.query(BackupSnapshots).with_entities(
                db.func.sum(BackupSnapshots.compressed_size)
            ).scalar() or 0
            
            storage_mb = total_storage / (1024 * 1024)
            
            return {
                'total_backups': total_backups,
                'total_snapshots': total_snapshots,
                'recent_backups_24h': recent_backups,
                'storage_used_mb': round(storage_mb, 2),
                'backup_directory': self.backup_dir
            }
            
        except Exception as e:
            print(f"❌ Error getting backup statistics: {e}")
            return {
                'total_backups': 0,
                'total_snapshots': 0,
                'recent_backups_24h': 0,
                'storage_used_mb': 0.0,
                'backup_directory': self.backup_dir
            }


@contextmanager
def auto_backup_context(backup_system: PostgreSQLBackupSystem, 
                       table_name: str, record_id: int, operation: str,
                       old_data: Dict[str, Any] = None, new_data: Dict[str, Any] = None,
                       user_id: str = None, source: str = "web_app"):
    """
    Context manager for automatic backup before operations
    
    Usage:
        with auto_backup_context(backup_system, 'main_lipids', 123, 'UPDATE', old_data, new_data):
            # Perform your database operation here
            lipid.lipid_name = "New Name"
            db.session.commit()
    """
    backup_id = None
    try:
        # Create backup before operation
        backup_id = backup_system.backup_before_change(
            table_name=table_name,
            record_id=record_id,
            operation=operation,
            old_data=old_data,
            new_data=new_data,
            user_id=user_id,
            source=source
        )
        print(f"✅ Operation completed, backup {backup_id} created")
        
        yield backup_id
        
    except Exception as e:
        print(f"❌ Operation failed, backup {backup_id} may be incomplete: {e}")
        raise e
    finally:
        print("✅ Context completed successfully")


# Global backup system instance
backup_system = PostgreSQLBackupSystem()


def init_backup_system(app):
    """Initialize backup system with Flask app"""
    backup_system.init_app(app)
    return backup_system