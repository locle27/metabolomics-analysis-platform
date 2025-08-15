"""
Comprehensive Database Backup and History System
Automatically backs up data before any changes and tracks complete history
"""

import os
import json
import sqlite3
import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import gzip
import pickle
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import threading
import time

@dataclass
class BackupRecord:
    """Individual backup record"""
    backup_id: str
    table_name: str
    record_id: int
    operation: str  # 'INSERT', 'UPDATE', 'DELETE'
    old_data: Optional[Dict[str, Any]]
    new_data: Optional[Dict[str, Any]]
    timestamp: float
    user_id: Optional[str]
    source: str  # 'web_app', 'api', 'admin'
    backup_hash: str

@dataclass
class BackupSnapshot:
    """Complete database snapshot"""
    snapshot_id: str
    timestamp: float
    description: str
    tables_count: int
    records_count: int
    compressed_size: int
    file_path: str
    backup_hash: str

class DatabaseBackupSystem:
    """
    Complete database backup and history tracking system
    """
    
    def __init__(self, main_db_url: str, backup_db_path: str = None):
        self.main_db_url = main_db_url
        self.backup_db_path = backup_db_path or "metabolomics_backup_system.db"
        self.backup_dir = Path("database_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize backup database
        self.setup_backup_database()
        
        # Create main database session
        self.main_engine = create_engine(main_db_url)
        MainSession = sessionmaker(bind=self.main_engine)
        self.main_session = MainSession()
        
        print(f"✅ Backup system initialized")
        print(f"   Main DB: {main_db_url}")
        print(f"   Backup DB: {self.backup_db_path}")
        print(f"   Backup Dir: {self.backup_dir}")
    
    def setup_backup_database(self):
        """Create backup database with all necessary tables"""
        self.backup_conn = sqlite3.connect(self.backup_db_path, check_same_thread=False)
        self.backup_conn.execute("PRAGMA journal_mode = WAL")
        self.backup_conn.execute("PRAGMA synchronous = NORMAL")
        
        # Create backup history table
        self.backup_conn.execute("""
            CREATE TABLE IF NOT EXISTS backup_history (
                backup_id TEXT PRIMARY KEY,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                operation TEXT NOT NULL CHECK(operation IN ('INSERT', 'UPDATE', 'DELETE')),
                old_data TEXT,  -- JSON string
                new_data TEXT,  -- JSON string
                timestamp REAL NOT NULL,
                user_id TEXT,
                source TEXT NOT NULL,
                backup_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for backup_history
        self.backup_conn.execute("CREATE INDEX IF NOT EXISTS idx_backup_table_name ON backup_history(table_name)")
        self.backup_conn.execute("CREATE INDEX IF NOT EXISTS idx_backup_record_id ON backup_history(record_id)")
        self.backup_conn.execute("CREATE INDEX IF NOT EXISTS idx_backup_timestamp ON backup_history(timestamp)")
        self.backup_conn.execute("CREATE INDEX IF NOT EXISTS idx_backup_operation ON backup_history(operation)")
        
        # Create snapshots table
        self.backup_conn.execute("""
            CREATE TABLE IF NOT EXISTS backup_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,
                description TEXT NOT NULL,
                tables_count INTEGER NOT NULL,
                records_count INTEGER NOT NULL,
                compressed_size INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                backup_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for snapshots
        self.backup_conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON backup_snapshots(timestamp)")
        
        # Create backup statistics table
        self.backup_conn.execute("""
            CREATE TABLE IF NOT EXISTS backup_stats (
                stat_date DATE PRIMARY KEY,
                backups_created INTEGER DEFAULT 0,
                data_changed_mb REAL DEFAULT 0,
                snapshots_created INTEGER DEFAULT 0,
                total_backup_size_mb REAL DEFAULT 0
            )
        """)
        
        self.backup_conn.commit()
        print("✅ Backup database schema created")
    
    def generate_backup_id(self) -> str:
        """Generate unique backup ID"""
        import uuid
        timestamp = str(time.time())
        random_uuid = str(uuid.uuid4())
        thread_id = str(threading.current_thread().ident)
        hash_input = f"{timestamp}_{thread_id}_{random_uuid}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    def calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash for data integrity"""
        if not data:
            return ""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def backup_before_change(self, table_name: str, record_id: int, 
                           operation: str, old_data: Dict[str, Any] = None, 
                           new_data: Dict[str, Any] = None,
                           user_id: str = None, source: str = "web_app") -> str:
        """
        Create backup record before any data change
        """
        timestamp = time.time()
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                backup_id = self.generate_backup_id()
                
                # Create backup record
                backup_record = BackupRecord(
                    backup_id=backup_id,
                    table_name=table_name,
                    record_id=record_id,
                    operation=operation,
                    old_data=old_data,
                    new_data=new_data,
                    timestamp=timestamp,
                    user_id=user_id,
                    source=source,
                    backup_hash=self.calculate_data_hash(old_data or new_data)
                )
                
                # Store in backup database
                self.backup_conn.execute("""
                    INSERT INTO backup_history (
                        backup_id, table_name, record_id, operation,
                        old_data, new_data, timestamp, user_id, source, backup_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    backup_record.backup_id,
                    backup_record.table_name,
                    backup_record.record_id,
                    backup_record.operation,
                    json.dumps(backup_record.old_data) if backup_record.old_data else None,
                    json.dumps(backup_record.new_data) if backup_record.new_data else None,
                    backup_record.timestamp,
                    backup_record.user_id,
                    backup_record.source,
                    backup_record.backup_hash
                ))
                
                # If we get here, the insert was successful
                break
                
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: backup_history.backup_id" in str(e) and attempt < max_retries - 1:
                    print(f"⚠️ Backup ID collision (attempt {attempt + 1}), retrying...")
                    time.sleep(0.001)  # Small delay before retry
                    continue
                else:
                    raise e
        self.backup_conn.commit()
        
        print(f"🔄 Backup created: {operation} on {table_name}[{record_id}] -> {backup_id}")
        return backup_id
    
    def get_current_record_data(self, table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
        """Get current data for a record from main database"""
        try:
            if table_name == 'main_lipids':
                query = "SELECT * FROM main_lipids WHERE lipid_id = :id"
            elif table_name == 'annotated_ions':
                query = "SELECT * FROM annotated_ions WHERE ion_id = :id"
            elif table_name == 'lipid_classes':
                query = "SELECT * FROM lipid_classes WHERE class_id = :id"
            else:
                return None
            
            result = self.main_session.execute(text(query), {"id": record_id})
            row = result.fetchone()
            
            if row:
                # Convert to dictionary
                columns = result.keys()
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            print(f"❌ Error getting current data: {e}")
            return None
    
    def create_full_snapshot(self, description: str = None) -> str:
        """Create complete database snapshot"""
        snapshot_id = f"snapshot_{int(time.time())}"
        timestamp = time.time()
        description = description or f"Auto snapshot {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Export all main database tables
        snapshot_data = {}
        tables_count = 0
        records_count = 0
        
        # Get all tables data
        tables = ['lipid_classes', 'main_lipids', 'annotated_ions']
        
        for table in tables:
            try:
                result = self.main_session.execute(text(f"SELECT * FROM {table}"))
                rows = result.fetchall()
                columns = result.keys()
                
                table_data = []
                for row in rows:
                    table_data.append(dict(zip(columns, row)))
                
                snapshot_data[table] = table_data
                tables_count += 1
                records_count += len(table_data)
                
                print(f"📊 Exported {table}: {len(table_data)} records")
                
            except Exception as e:
                print(f"❌ Error exporting {table}: {e}")
        
        # Add metadata
        snapshot_data['_metadata'] = {
            'snapshot_id': snapshot_id,
            'timestamp': timestamp,
            'description': description,
            'created_by': 'backup_system',
            'tables': tables,
            'export_date': datetime.datetime.now().isoformat()
        }
        
        # Compress and save
        file_path = self.backup_dir / f"{snapshot_id}.pkl.gz"
        
        with gzip.open(file_path, 'wb') as f:
            pickle.dump(snapshot_data, f)
        
        # Get file size
        compressed_size = file_path.stat().st_size
        
        # Calculate hash
        backup_hash = self.calculate_data_hash(snapshot_data['_metadata'])
        
        # Create snapshot record
        snapshot = BackupSnapshot(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            description=description,
            tables_count=tables_count,
            records_count=records_count,
            compressed_size=compressed_size,
            file_path=str(file_path),
            backup_hash=backup_hash
        )
        
        # Store snapshot info
        self.backup_conn.execute("""
            INSERT INTO backup_snapshots (
                snapshot_id, timestamp, description, tables_count,
                records_count, compressed_size, file_path, backup_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.snapshot_id,
            snapshot.timestamp,
            snapshot.description,
            snapshot.tables_count,
            snapshot.records_count,
            snapshot.compressed_size,
            snapshot.file_path,
            snapshot.backup_hash
        ))
        self.backup_conn.commit()
        
        print(f"📸 Snapshot created: {snapshot_id}")
        print(f"   Records: {records_count}, Size: {compressed_size/1024/1024:.2f} MB")
        
        return snapshot_id
    
    def get_backup_history(self, table_name: str = None, record_id: int = None, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get backup history with optional filtering"""
        query = "SELECT * FROM backup_history WHERE 1=1"
        params = []
        
        if table_name:
            query += " AND table_name = ?"
            params.append(table_name)
        
        if record_id:
            query += " AND record_id = ?"
            params.append(record_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.backup_conn.execute(query, params)
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'backup_id': row[0],
                'table_name': row[1],
                'record_id': row[2],
                'operation': row[3],
                'old_data': json.loads(row[4]) if row[4] else None,
                'new_data': json.loads(row[5]) if row[5] else None,
                'timestamp': row[6],
                'user_id': row[7],
                'source': row[8],
                'backup_hash': row[9],
                'created_at': row[10]
            })
        
        return history
    
    def get_snapshots(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get available snapshots"""
        cursor = self.backup_conn.execute("""
            SELECT * FROM backup_snapshots 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        snapshots = []
        for row in cursor.fetchall():
            snapshots.append({
                'snapshot_id': row[0],
                'timestamp': row[1],
                'description': row[2],
                'tables_count': row[3],
                'records_count': row[4],
                'compressed_size': row[5],
                'file_path': row[6],
                'backup_hash': row[7],
                'created_at': row[8]
            })
        
        return snapshots
    
    def restore_from_snapshot(self, snapshot_id: str, tables: List[str] = None) -> bool:
        """Restore data from snapshot (USE WITH CAUTION)"""
        try:
            # Get snapshot info
            cursor = self.backup_conn.execute("""
                SELECT file_path FROM backup_snapshots WHERE snapshot_id = ?
            """, (snapshot_id,))
            
            row = cursor.fetchone()
            if not row:
                print(f"❌ Snapshot {snapshot_id} not found")
                return False
            
            file_path = Path(row[0])
            if not file_path.exists():
                print(f"❌ Snapshot file not found: {file_path}")
                return False
            
            # Load snapshot data
            with gzip.open(file_path, 'rb') as f:
                snapshot_data = pickle.load(f)
            
            tables_to_restore = tables or ['lipid_classes', 'main_lipids', 'annotated_ions']
            
            print(f"⚠️  WARNING: This will overwrite current data!")
            print(f"   Restoring tables: {tables_to_restore}")
            
            # This is a dangerous operation - implement with proper safeguards
            # For now, just print what would be restored
            for table in tables_to_restore:
                if table in snapshot_data:
                    records = len(snapshot_data[table])
                    print(f"   Would restore {table}: {records} records")
            
            print("🔒 Restoration not implemented (safety measure)")
            print("   Use manual database restoration for safety")
            
            return True
            
        except Exception as e:
            print(f"❌ Error restoring snapshot: {e}")
            return False
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup system statistics"""
        # Total backups
        cursor = self.backup_conn.execute("SELECT COUNT(*) FROM backup_history")
        total_backups = cursor.fetchone()[0]
        
        # Total snapshots
        cursor = self.backup_conn.execute("SELECT COUNT(*) FROM backup_snapshots")
        total_snapshots = cursor.fetchone()[0]
        
        # Recent activity (last 24 hours)
        day_ago = time.time() - 86400
        cursor = self.backup_conn.execute("""
            SELECT COUNT(*) FROM backup_history WHERE timestamp > ?
        """, (day_ago,))
        recent_backups = cursor.fetchone()[0]
        
        # Storage usage
        total_size = 0
        if self.backup_dir.exists():
            for file in self.backup_dir.glob("*.pkl.gz"):
                total_size += file.stat().st_size
        
        # Database size
        backup_db_size = Path(self.backup_db_path).stat().st_size if Path(self.backup_db_path).exists() else 0
        
        return {
            'total_backups': total_backups,
            'total_snapshots': total_snapshots,
            'recent_backups_24h': recent_backups,
            'storage_used_mb': (total_size + backup_db_size) / 1024 / 1024,
            'backup_db_size_mb': backup_db_size / 1024 / 1024,
            'snapshots_size_mb': total_size / 1024 / 1024,
            'backup_directory': str(self.backup_dir),
            'backup_database': self.backup_db_path
        }
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """Clean up old backup records"""
        cutoff_time = time.time() - (days_to_keep * 86400)
        
        cursor = self.backup_conn.execute("""
            DELETE FROM backup_history WHERE timestamp < ?
        """, (cutoff_time,))
        
        deleted_count = cursor.rowcount
        self.backup_conn.commit()
        
        print(f"🧹 Cleaned up {deleted_count} old backup records (older than {days_to_keep} days)")
        return deleted_count
    
    def close(self):
        """Close database connections"""
        if hasattr(self, 'backup_conn'):
            self.backup_conn.close()
        if hasattr(self, 'main_session'):
            self.main_session.close()

# Context manager for automatic backup
class AutoBackupContext:
    """Context manager that automatically creates backups before data changes"""
    
    def __init__(self, backup_system: DatabaseBackupSystem, table_name: str, 
                 record_id: int, operation: str, user_id: str = None):
        self.backup_system = backup_system
        self.table_name = table_name
        self.record_id = record_id
        self.operation = operation
        self.user_id = user_id
        self.backup_id = None
    
    def __enter__(self):
        # Get current data before change
        old_data = self.backup_system.get_current_record_data(self.table_name, self.record_id)
        
        # Create backup
        self.backup_id = self.backup_system.backup_before_change(
            table_name=self.table_name,
            record_id=self.record_id,
            operation=self.operation,
            old_data=old_data,
            user_id=self.user_id
        )
        
        return self.backup_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"⚠️  Operation failed, backup {self.backup_id} preserved")
        else:
            print(f"✅ Operation completed, backup {self.backup_id} created")