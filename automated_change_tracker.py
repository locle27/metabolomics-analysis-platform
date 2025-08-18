#!/usr/bin/env python3
"""
🚀 AUTOMATED CHANGE TRACKING SYSTEM
Advanced file monitoring and version control for metabolomics platform

Features:
- Real-time file monitoring with watchdog
- Automated backups on changes
- Git integration for version history
- Database logging of all changes
- Web dashboard for change visualization
- Error detection and recovery
- Developer-focused change analysis

For Main Admin: loc22100302@gmail.com only
"""

import os
import sys
import time
import shutil
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
import subprocess
import sqlite3
from dataclasses import dataclass, asdict

# File monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️ Watchdog not available - install with: pip install watchdog")

@dataclass
class ChangeRecord:
    """Data structure for tracking file changes"""
    timestamp: str
    file_path: str
    change_type: str  # created, modified, deleted, moved
    file_size: int
    file_hash: str
    backup_path: Optional[str]
    git_commit: Optional[str]
    error_detected: bool
    change_severity: str  # low, medium, high, critical
    description: str

class ProjectChangeTracker(FileSystemEventHandler):
    """Advanced file system change tracker with automated backups"""
    
    def __init__(self, project_root: str, backup_root: str):
        self.project_root = Path(project_root).resolve()
        self.backup_root = Path(backup_root).resolve()
        self.db_path = self.project_root / "change_history.db"
        
        # Create backup directory structure
        self.backup_root.mkdir(parents=True, exist_ok=True)
        (self.backup_root / "automated_backups").mkdir(exist_ok=True)
        (self.backup_root / "error_snapshots").mkdir(exist_ok=True)
        (self.backup_root / "daily_snapshots").mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # File filters
        self.monitored_extensions = {
            '.py', '.html', '.css', '.js', '.json', '.md', '.txt', '.yml', '.yaml',
            '.sql', '.env', '.toml', '.cfg', '.ini', '.sh', '.bat'
        }
        
        self.ignore_patterns = {
            '__pycache__', '.git', '.env', 'node_modules', '.vscode',
            'venv', 'env', '.pyc', '.log', '.tmp', 'change_history.db'
        }
        
        print(f"🔍 Change tracker initialized for: {self.project_root}")
        print(f"💾 Backups will be stored in: {self.backup_root}")
    
    def _init_database(self):
        """Initialize SQLite database for change tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS change_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    file_size INTEGER,
                    file_hash TEXT,
                    backup_path TEXT,
                    git_commit TEXT,
                    error_detected BOOLEAN DEFAULT FALSE,
                    change_severity TEXT DEFAULT 'low',
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    total_changes INTEGER DEFAULT 0,
                    files_modified INTEGER DEFAULT 0,
                    errors_detected INTEGER DEFAULT 0,
                    backups_created INTEGER DEFAULT 0,
                    git_commits INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON change_history(timestamp);
                CREATE INDEX IF NOT EXISTS idx_file_path ON change_history(file_path);
                CREATE INDEX IF NOT EXISTS idx_change_type ON change_history(change_type);
            """)
    
    def _should_monitor_file(self, file_path: Path) -> bool:
        """Check if file should be monitored"""
        try:
            # Check if file exists and is actually a file
            if not file_path.exists() or not file_path.is_file():
                return False
            
            # Check extension
            if file_path.suffix.lower() not in self.monitored_extensions:
                return False
            
            # Check ignore patterns
            for part in file_path.parts:
                if any(ignore in part for ignore in self.ignore_patterns):
                    return False
            
            # Check if file is in project root
            try:
                file_path.relative_to(self.project_root)
            except ValueError:
                return False
            
            return True
        except Exception as e:
            print(f"⚠️ Error checking file {file_path}: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except Exception as e:
            print(f"⚠️ Error calculating hash for {file_path}: {e}")
            return "unknown"
    
    def _create_backup(self, file_path: Path, change_type: str) -> Optional[str]:
        """Create timestamped backup of changed file"""
        try:
            if not file_path.exists():
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            relative_path = file_path.relative_to(self.project_root)
            
            # Create backup directory structure
            backup_dir = self.backup_root / "automated_backups" / relative_path.parent
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup filename
            backup_name = f"{file_path.stem}_{timestamp}_{change_type}{file_path.suffix}"
            backup_path = backup_dir / backup_name
            
            # Copy file
            shutil.copy2(file_path, backup_path)
            
            print(f"💾 Backup created: {backup_name}")
            return str(backup_path.relative_to(self.backup_root))
            
        except Exception as e:
            print(f"❌ Backup failed for {file_path}: {e}")
            return None
    
    def _detect_errors(self, file_path: Path, change_type: str) -> tuple[bool, str]:
        """Analyze file for potential errors"""
        try:
            if not file_path.exists():
                return False, "low"
            
            error_indicators = []
            severity = "low"
            
            # Check Python files for syntax errors
            if file_path.suffix == '.py':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, str(file_path), 'exec')
                except SyntaxError as e:
                    error_indicators.append(f"Python syntax error: {e}")
                    severity = "critical"
                except Exception as e:
                    error_indicators.append(f"Python compilation error: {e}")
                    severity = "high"
            
            # Check for common error patterns
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                
                # Error keywords
                error_keywords = ['error', 'exception', 'traceback', 'failed', 'crash']
                critical_keywords = ['critical', 'fatal', 'emergency', 'panic']
                
                for keyword in critical_keywords:
                    if keyword in content:
                        severity = "critical"
                        error_indicators.append(f"Critical keyword found: {keyword}")
                
                for keyword in error_keywords:
                    if keyword in content and severity == "low":
                        severity = "medium"
                        error_indicators.append(f"Error keyword found: {keyword}")
                
            except Exception:
                pass  # Skip content analysis if file can't be read
            
            # Check file size changes
            if file_path.stat().st_size == 0:
                error_indicators.append("File is empty")
                severity = "high"
            
            return len(error_indicators) > 0, severity
            
        except Exception as e:
            print(f"⚠️ Error detection failed for {file_path}: {e}")
            return False, "low"
    
    def _create_git_commit(self, file_path: Path, change_type: str) -> Optional[str]:
        """Create automatic git commit for changes"""
        try:
            # Check if git is available and we're in a git repo
            result = subprocess.run(['git', 'status'], 
                                  cwd=self.project_root, 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode != 0:
                return None
            
            # Add file to git
            subprocess.run(['git', 'add', str(file_path)], 
                          cwd=self.project_root, 
                          check=True)
            
            # Create commit message
            relative_path = file_path.relative_to(self.project_root)
            commit_msg = f"🤖 AUTO: {change_type} {relative_path}"
            
            # Commit
            result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                                  cwd=self.project_root, 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                # Get commit hash
                hash_result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                           cwd=self.project_root, 
                                           capture_output=True, 
                                           text=True)
                commit_hash = hash_result.stdout.strip()[:8]
                print(f"📝 Git commit created: {commit_hash}")
                return commit_hash
            
        except Exception as e:
            print(f"⚠️ Git commit failed: {e}")
        
        return None
    
    def _log_change(self, change_record: ChangeRecord):
        """Log change to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO change_history 
                    (timestamp, file_path, change_type, file_size, file_hash, 
                     backup_path, git_commit, error_detected, change_severity, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    change_record.timestamp,
                    change_record.file_path,
                    change_record.change_type,
                    change_record.file_size,
                    change_record.file_hash,
                    change_record.backup_path,
                    change_record.git_commit,
                    change_record.error_detected,
                    change_record.change_severity,
                    change_record.description
                ))
                
                # Update daily stats
                today = datetime.now().strftime("%Y-%m-%d")
                conn.execute("""
                    INSERT OR IGNORE INTO daily_stats (date) VALUES (?)
                """, (today,))
                
                conn.execute("""
                    UPDATE daily_stats SET 
                        total_changes = total_changes + 1,
                        files_modified = files_modified + 1,
                        errors_detected = errors_detected + ?,
                        backups_created = backups_created + ?,
                        git_commits = git_commits + ?
                    WHERE date = ?
                """, (
                    1 if change_record.error_detected else 0,
                    1 if change_record.backup_path else 0,
                    1 if change_record.git_commit else 0,
                    today
                ))
                
        except Exception as e:
            print(f"❌ Database logging failed: {e}")
    
    def _process_change(self, file_path: Path, change_type: str):
        """Process a file change with full automation"""
        try:
            if not self._should_monitor_file(file_path):
                return
            
            print(f"🔍 Processing {change_type}: {file_path.name}")
            
            # Gather file information
            timestamp = datetime.now().isoformat()
            file_size = file_path.stat().st_size if file_path.exists() else 0
            file_hash = self._calculate_file_hash(file_path) if file_path.exists() else "deleted"
            
            # Create backup
            backup_path = self._create_backup(file_path, change_type)
            
            # Detect errors
            error_detected, severity = self._detect_errors(file_path, change_type)
            
            # Create git commit
            git_commit = self._create_git_commit(file_path, change_type)
            
            # Generate description
            relative_path = file_path.relative_to(self.project_root)
            description = f"{change_type.title()} {relative_path} ({file_size} bytes)"
            
            if error_detected:
                description += f" [⚠️ {severity.upper()} SEVERITY]"
            
            # Create change record
            change_record = ChangeRecord(
                timestamp=timestamp,
                file_path=str(relative_path),
                change_type=change_type,
                file_size=file_size,
                file_hash=file_hash,
                backup_path=backup_path,
                git_commit=git_commit,
                error_detected=error_detected,
                change_severity=severity,
                description=description
            )
            
            # Log to database
            self._log_change(change_record)
            
            # Print summary
            status_icon = "⚠️" if error_detected else "✅"
            print(f"{status_icon} {description}")
            
            if error_detected and severity in ['high', 'critical']:
                self._create_error_snapshot(file_path)
            
        except Exception as e:
            print(f"❌ Error processing change for {file_path}: {e}")
    
    def _create_error_snapshot(self, file_path: Path):
        """Create special snapshot when errors are detected"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_dir = self.backup_root / "error_snapshots" / timestamp
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy the problematic file
            if file_path.exists():
                shutil.copy2(file_path, snapshot_dir / file_path.name)
            
            # Create error report
            error_report = {
                "timestamp": timestamp,
                "file": str(file_path.relative_to(self.project_root)),
                "detection_reason": "Automated error detection",
                "file_size": file_path.stat().st_size if file_path.exists() else 0,
                "created_by": "AutoChangeTracker"
            }
            
            with open(snapshot_dir / "error_report.json", 'w') as f:
                json.dump(error_report, f, indent=2)
            
            print(f"🚨 Error snapshot created: {timestamp}")
            
        except Exception as e:
            print(f"❌ Error snapshot creation failed: {e}")
    
    # Watchdog event handlers
    def on_modified(self, event):
        if not event.is_directory:
            self._process_change(Path(event.src_path), "modified")
    
    def on_created(self, event):
        if not event.is_directory:
            self._process_change(Path(event.src_path), "created")
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._process_change(Path(event.src_path), "deleted")
    
    def on_moved(self, event):
        if not event.is_directory:
            self._process_change(Path(event.dest_path), "moved")

class ChangeTrackerService:
    """Service to run the change tracker in background"""
    
    def __init__(self, project_root: str, backup_root: str):
        self.project_root = project_root
        self.backup_root = backup_root
        self.tracker = ProjectChangeTracker(project_root, backup_root)
        self.observer = None
        self.running = False
    
    def start(self):
        """Start monitoring service"""
        if not WATCHDOG_AVAILABLE:
            print("❌ Cannot start - watchdog not available")
            return False
        
        try:
            self.observer = Observer()
            self.observer.schedule(self.tracker, self.project_root, recursive=True)
            self.observer.start()
            self.running = True
            
            print("🚀 Automated Change Tracking Service STARTED")
            print(f"📁 Monitoring: {self.project_root}")
            print(f"💾 Backups: {self.backup_root}")
            print("🔍 Watching for file changes...")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start monitoring service: {e}")
            return False
    
    def stop(self):
        """Stop monitoring service"""
        if self.observer and self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            print("🛑 Change tracking service stopped")
    
    def get_recent_changes(self, hours: int = 24) -> List[Dict]:
        """Get recent changes from database"""
        try:
            with sqlite3.connect(self.tracker.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM change_history 
                    WHERE datetime(created_at) > datetime('now', '-{} hours')
                    ORDER BY created_at DESC
                    LIMIT 100
                """.format(hours))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"❌ Error getting recent changes: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get change tracking statistics"""
        try:
            with sqlite3.connect(self.tracker.db_path) as conn:
                stats = {}
                
                # Total changes
                cursor = conn.execute("SELECT COUNT(*) FROM change_history")
                stats['total_changes'] = cursor.fetchone()[0]
                
                # Today's changes
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM change_history 
                    WHERE date(created_at) = date('now')
                """)
                stats['today_changes'] = cursor.fetchone()[0]
                
                # Error count
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM change_history 
                    WHERE error_detected = 1
                """)
                stats['total_errors'] = cursor.fetchone()[0]
                
                # Recent activity
                cursor = conn.execute("""
                    SELECT change_type, COUNT(*) as count 
                    FROM change_history 
                    WHERE datetime(created_at) > datetime('now', '-24 hours')
                    GROUP BY change_type
                """)
                stats['recent_activity'] = dict(cursor.fetchall())
                
                # Service status
                stats['service_running'] = self.running
                stats['monitoring_path'] = str(self.project_root)
                stats['backup_path'] = str(self.backup_root)
                
                return stats
                
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}

# Global service instance
_service_instance = None

def get_change_tracker_service():
    """Get or create the global change tracker service"""
    global _service_instance
    
    if _service_instance is None:
        project_root = os.path.dirname(os.path.abspath(__file__))
        backup_root = os.path.join(os.path.dirname(project_root), "automated_change_backups")
        _service_instance = ChangeTrackerService(project_root, backup_root)
    
    return _service_instance

def start_monitoring():
    """Start the change monitoring service"""
    service = get_change_tracker_service()
    return service.start()

def stop_monitoring():
    """Stop the change monitoring service"""
    service = get_change_tracker_service()
    service.stop()

if __name__ == "__main__":
    # Command line interface
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Change Tracking System")
    parser.add_argument("--start", action="store_true", help="Start monitoring service")
    parser.add_argument("--stop", action="store_true", help="Stop monitoring service")
    parser.add_argument("--status", action="store_true", help="Show service status")
    parser.add_argument("--recent", type=int, default=24, help="Show recent changes (hours)")
    
    args = parser.parse_args()
    
    service = get_change_tracker_service()
    
    if args.start:
        if service.start():
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping service...")
                service.stop()
    
    elif args.stop:
        service.stop()
    
    elif args.status:
        stats = service.get_stats()
        print("\n📊 CHANGE TRACKER STATUS")
        print("=" * 40)
        for key, value in stats.items():
            print(f"{key}: {value}")
    
    elif args.recent:
        changes = service.get_recent_changes(args.recent)
        print(f"\n📋 RECENT CHANGES ({args.recent} hours)")
        print("=" * 50)
        for change in changes[:10]:  # Show last 10
            print(f"⏰ {change['timestamp']}")
            print(f"📁 {change['file_path']}")
            print(f"🔄 {change['change_type']}")
            if change['error_detected']:
                print(f"⚠️ ERROR DETECTED ({change['change_severity']})")
            print("-" * 30)
    
    else:
        parser.print_help()