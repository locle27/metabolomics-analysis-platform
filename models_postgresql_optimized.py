"""
Optimized PostgreSQL Models with Eager Loading
Fixes N+1 query problems that caused original performance issues
"""

import os
import json
from functools import lru_cache
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func, text, Column, String, Integer, Float, Text, Boolean, DateTime, JSON, CheckConstraint, Index
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import time
import uuid
from datetime import datetime, timedelta

# SQLAlchemy instance
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255))
    picture = db.Column(db.String(500))
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(50), default='user', nullable=False)  # user, manager, admin
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime)
    
    # Security fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    last_password_change = db.Column(db.DateTime)
    auth_method = db.Column(db.String(50), default='password')  # oauth, password, demo
    
    # Verification tokens
    verification_tokens = db.relationship('VerificationToken', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username} ({self.email}): {self.role}>'
    
    # Flask-Login required methods  
    def get_id(self):
        return str(self.id)
    
    # Role checking methods
    def is_admin(self):
        return self.role == 'admin'
    
    def is_manager(self):
        return self.role in ['admin', 'manager']
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
        self.last_password_change = datetime.utcnow()
        self.auth_method = 'password'
        
    def check_password(self, password):
        """Check if provided password matches hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
        
    def is_account_locked(self):
        """Check if account is temporarily locked due to failed attempts"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
        
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts += 1
        
    def unlock_account(self):
        """Unlock account and reset failed attempts"""
        self.locked_until = None
        self.failed_login_attempts = 0
        
    def generate_verification_token(self, token_type='email_verification', expires_delta=None):
        """Generate a new verification token"""
        # Set default expiration based on token type
        if expires_delta is None:
            if token_type == 'password_reset':
                expires_delta = timedelta(hours=2)  # Password reset expires in 2 hours
            else:
                expires_delta = timedelta(hours=24)  # Email verification expires in 24 hours
        
        # Deactivate existing tokens of the same type
        existing_tokens = VerificationToken.query.filter_by(
            user_id=self.id, 
            token_type=token_type, 
            is_used=False
        ).all()
        for token in existing_tokens:
            token.is_used = True
            
        # Create new token
        token = VerificationToken(
            user_id=self.id,
            token=str(uuid.uuid4()),
            token_type=token_type,
            expires_at=datetime.utcnow() + expires_delta
        )
        db.session.add(token)
        return token
        
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'auth_method': self.auth_method
        }

class VerificationToken(db.Model):
    __tablename__ = 'verification_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    token_type = db.Column(db.String(50), nullable=False)  # email_verification, password_reset
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    
    # Relationship
    user = db.relationship('User', back_populates='verification_tokens')
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        return not self.is_used and datetime.utcnow() < self.expires_at
        
    def use_token(self):
        """Mark token as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()

class LipidClass(db.Model):
    __tablename__ = 'lipid_classes'
    
    class_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_name = db.Column(db.String(255), nullable=False, unique=True)
    class_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationship to lipids
    main_lipids = db.relationship('MainLipid', back_populates='lipid_class', lazy='select')
    
    def to_dict(self):
        return {
            'class_id': self.class_id,
            'class_name': self.class_name,
            'class_description': self.class_description
        }

class MainLipid(db.Model):
    __tablename__ = 'main_lipids'
    
    lipid_id = db.Column(db.Integer, primary_key=True)
    lipid_name = db.Column(db.String(255), nullable=False)
    api_code = db.Column(db.String(255))
    class_id = db.Column(db.Integer, db.ForeignKey('lipid_classes.class_id'))
    retention_time = db.Column(db.Float)
    precursor_ion = db.Column(db.String(255))
    product_ion = db.Column(db.String(255))
    collision_energy = db.Column(db.Integer)
    polarity = db.Column(db.String(255), default='Positive')
    internal_standard = db.Column(db.String(255))
    xic_data = db.Column(db.JSON)
    extraction_timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    extraction_method = db.Column(db.String(255))
    extraction_success = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Optimized relationships with proper loading strategies
    lipid_class = db.relationship('LipidClass', back_populates='main_lipids', lazy='select')
    annotated_ions = db.relationship('AnnotatedIon', back_populates='main_lipid', 
                                   lazy='select', cascade='all, delete-orphan')
    
    def to_dict(self, include_xic=False, include_ions=False):
        result = {
            'lipid_id': self.lipid_id,
            'lipid_name': self.lipid_name,
            'api_code': self.api_code,
            'class_id': self.class_id,
            'retention_time': self.retention_time,
            'precursor_ion': self.precursor_ion,
            'product_ion': self.product_ion,
            'collision_energy': self.collision_energy,
            'polarity': self.polarity,
            'extraction_success': self.extraction_success
        }
        
        if include_xic and self.xic_data:
            result['xic_data'] = self.xic_data
            
        if include_ions:
            result['annotated_ions'] = [ion.to_dict() for ion in self.annotated_ions]
            
        return result

class AnnotatedIon(db.Model):
    __tablename__ = 'annotated_ions'
    
    ion_id = db.Column(db.Integer, primary_key=True)
    main_lipid_id = db.Column(db.Integer, db.ForeignKey('main_lipids.lipid_id'))
    ion_lipid_name = db.Column(db.String(255))
    ion_lipidcode = db.Column(db.String(255))
    annotation_type = db.Column(db.String(255))
    retention_time = db.Column(db.Float)
    precursor_ion = db.Column(db.String(255))
    product_ion = db.Column(db.String(255))
    collision_energy = db.Column(db.Integer)
    polarity = db.Column(db.String(255))
    response_factor = db.Column(db.Float, default=1.0)
    int_start = db.Column(db.Float)
    int_end = db.Column(db.Float)
    is_main_lipid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationship back to main lipid
    main_lipid = db.relationship('MainLipid', back_populates='annotated_ions', lazy='select')
    
    def to_dict(self):
        return {
            'ion_id': self.ion_id,
            'main_lipid_id': self.main_lipid_id,
            'ion_lipid_name': self.ion_lipid_name,
            'ion_lipidcode': self.ion_lipidcode,
            'annotation_type': self.annotation_type,
            'retention_time': self.retention_time,
            'precursor_ion': self.precursor_ion,
            'product_ion': self.product_ion,
            'collision_energy': self.collision_energy,
            'polarity': self.polarity,
            'response_factor': self.response_factor,
            'int_start': self.int_start,
            'int_end': self.int_end,
            'is_main_lipid': self.is_main_lipid
        }


class OptimizedDataManager:
    """
    Optimized data access layer that fixes N+1 query problems
    """
    
    def __init__(self):
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
        self._last_cache_time = 0
    
    @lru_cache(maxsize=1)
    def get_all_lipids_optimized(self):
        """
        Get all lipids with proper eager loading - NO N+1 QUERIES
        This is equivalent to SQLite's cached approach but with PostgreSQL
        """
        start_time = time.time()
        
        # Single optimized query with all related data - show ALL lipids for management
        lipids = MainLipid.query.options(
            joinedload(MainLipid.lipid_class),          # JOIN to get class
            selectinload(MainLipid.annotated_ions)      # Separate optimized query for ions
        ).all()  # Remove filter to show all lipids including failed ones
        
        # Convert to dictionary format like SQLite version
        result = []
        for lipid in lipids:
            lipid_dict = {
                'lipid_id': lipid.lipid_id,
                'lipid_name': lipid.lipid_name,
                'api_code': lipid.api_code,
                'retention_time': lipid.retention_time,
                'precursor_ion': lipid.precursor_ion,
                'product_ion': lipid.product_ion,
                'collision_energy': lipid.collision_energy,
                'polarity': lipid.polarity,
                'internal_standard': lipid.internal_standard,
                'xic_peak_intensity': None,  # Placeholder - field not in current schema
                'class_name': lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown',
                'annotated_ions_count': len(lipid.annotated_ions),  # No additional query!
                'extraction_success': lipid.extraction_success  # Include extraction status
            }
            result.append(lipid_dict)
        
        query_time = time.time() - start_time
        print(f"✅ Optimized PostgreSQL query: {len(result)} lipids in {query_time:.3f}s")
        
        return result
    
    @lru_cache(maxsize=1)
    def get_lipid_classes_optimized(self):
        """
        Get lipid classes with counts using efficient SQL
        """
        # Single efficient query with COUNT
        classes_with_counts = db.session.query(
            LipidClass.class_name,
            func.count(MainLipid.lipid_id).label('count')
        ).outerjoin(MainLipid).group_by(
            LipidClass.class_id, LipidClass.class_name
        ).order_by(LipidClass.class_name).all()
        
        return [
            {'class_name': class_name, 'count': count}
            for class_name, count in classes_with_counts
        ]
    
    def get_lipid_chart_data_optimized(self, lipid_id):
        """
        Get chart data with optimized single query - NO N+1
        """
        # Single query with all related data
        lipid = MainLipid.query.options(
            joinedload(MainLipid.lipid_class),
            selectinload(MainLipid.annotated_ions)
        ).filter_by(lipid_id=lipid_id).first()
        
        if not lipid:
            return None
            
        return {
            'lipid_info': {
                'lipid_id': lipid.lipid_id,
                'lipid_name': lipid.lipid_name,
                'api_code': lipid.api_code,
                'retention_time': lipid.retention_time,
                'class_name': lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown'
            },
            'annotated_ions': [ion.to_dict() for ion in lipid.annotated_ions],
            'xic_data': lipid.xic_data
        }
    
    def get_database_stats(self):
        """
        Get database statistics with efficient queries
        """
        # Count ALL lipids (don't filter by extraction_success - field may not exist)
        total_lipids = MainLipid.query.count()
        total_ions = AnnotatedIon.query.count() 
        total_classes = LipidClass.query.count()
        
        return {
            'total_lipids': total_lipids,
            'total_annotated_ions': total_ions,
            'total_classes': total_classes,
            'database_type': 'PostgreSQL (Optimized)',
            'database_url': os.getenv('DATABASE_URL', 'Local PostgreSQL')
        }
    
    def search_lipids_optimized(self, query):
        """
        Search lipids with proper eager loading
        """
        lipids = MainLipid.query.options(
            joinedload(MainLipid.lipid_class)
        ).filter(
            MainLipid.lipid_name.ilike(f'%{query}%'),
            MainLipid.extraction_success == True
        ).all()
        
        return [
            {
                'lipid_id': lipid.lipid_id,
                'lipid_name': lipid.lipid_name,
                'api_code': lipid.api_code,
                'retention_time': lipid.retention_time,
                'class_name': lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown',
                'annotated_ions_count': len(lipid.annotated_ions)
            }
            for lipid in lipids
        ]
    
    def filter_by_class_optimized(self, class_name):
        """
        Filter by class with proper eager loading
        """
        lipids = MainLipid.query.options(
            joinedload(MainLipid.lipid_class),
            selectinload(MainLipid.annotated_ions)
        ).join(LipidClass).filter(
            LipidClass.class_name == class_name,
            MainLipid.extraction_success == True
        ).all()
        
        return [
            {
                'lipid_id': lipid.lipid_id,
                'lipid_name': lipid.lipid_name,
                'api_code': lipid.api_code,
                'retention_time': lipid.retention_time,
                'class_name': lipid.lipid_class.class_name,
                'annotated_ions_count': len(lipid.annotated_ions)
            }
            for lipid in lipids
        ]
    
    def get_lipids_sample(self, limit=3):
        """
        Get a small sample of lipids for homepage - ULTRA FAST
        """
        lipids = MainLipid.query.options(
            joinedload(MainLipid.lipid_class)
        ).filter(
            MainLipid.extraction_success == True
        ).limit(limit).all()
        
        return [
            {
                'lipid_id': lipid.lipid_id,
                'lipid_name': lipid.lipid_name,
                'api_code': lipid.api_code,
                'retention_time': lipid.retention_time,
                'class_name': lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown'
            }
            for lipid in lipids
        ]

# Create global optimized manager
optimized_manager = OptimizedDataManager()

# Compatibility functions
def get_db_stats():
    """Compatible with both app.py versions"""
    return optimized_manager.get_database_stats()

def get_lipids_by_class(class_name):
    """Optimized class filtering"""
    return optimized_manager.filter_by_class_optimized(class_name)

def search_lipids(query):
    """Optimized search"""
    return optimized_manager.search_lipids_optimized(query)

def init_db(app):
    """Initialize database"""
    db.init_app(app)
    return db

def create_all_tables():
    """Create all tables"""
    db.create_all()


# =====================================================
# BACKUP SYSTEM MODELS - PostgreSQL-based backup
# =====================================================

class BackupHistory(db.Model):
    """Track all data changes for backup/audit purposes"""
    __tablename__ = 'backup_history'
    
    backup_id = Column(String(16), primary_key=True)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    operation = Column(String(10), nullable=False, index=True)
    old_data = Column(JSON)  # JSONB for PostgreSQL
    new_data = Column(JSON)  # JSONB for PostgreSQL
    timestamp = Column(Float, nullable=False, index=True)
    user_id = Column(String(100))
    source = Column(String(50), nullable=False, default='web_app')
    backup_hash = Column(String(16), nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Add check constraint for operation
    __table_args__ = (
        CheckConstraint("operation IN ('INSERT', 'UPDATE', 'DELETE')", name='valid_operation'),
        Index('idx_backup_table_record', 'table_name', 'record_id'),
        Index('idx_backup_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f'<BackupHistory {self.backup_id}: {self.operation} on {self.table_name}[{self.record_id}]>'


class BackupSnapshots(db.Model):
    """Store full database snapshots"""
    __tablename__ = 'backup_snapshots'
    
    snapshot_id = Column(String(20), primary_key=True)
    timestamp = Column(Float, nullable=False, index=True)
    description = Column(Text, nullable=False)
    tables_count = Column(Integer, nullable=False)
    records_count = Column(Integer, nullable=False)
    compressed_size = Column(Integer, nullable=False)  # in bytes
    file_path = Column(String(500), nullable=False)
    backup_hash = Column(String(16), nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    def __repr__(self):
        return f'<BackupSnapshot {self.snapshot_id}: {self.records_count} records>'


class BackupStats(db.Model):
    """Daily backup statistics"""
    __tablename__ = 'backup_stats'
    
    stat_date = Column(DateTime, primary_key=True, default=func.current_date())
    backups_created = Column(Integer, default=0)
    data_changed_mb = Column(Float, default=0.0)
    snapshots_created = Column(Integer, default=0)
    total_backup_size_mb = Column(Float, default=0.0)




class ScheduleRequest(db.Model):
    """Model for consultation scheduling requests"""
    __tablename__ = 'schedule_requests'
    
    request_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    organization = db.Column(db.String(255))
    request_type = db.Column(db.String(100), nullable=False)  # consultation, demo, partnership, etc.
    message = db.Column(db.Text, nullable=False)
    preferred_date = db.Column(db.Date)
    preferred_time = db.Column(db.String(50))
    status = db.Column(db.String(50), default='pending', nullable=False)  # pending, contacted, scheduled, completed
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    contacted_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ScheduleRequest {self.request_id}: {self.full_name} ({self.status})>'
    
    def to_dict(self):
        return {
            'request_id': self.request_id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'organization': self.organization,
            'request_type': self.request_type,
            'message': self.message,
            'preferred_date': self.preferred_date.isoformat() if self.preferred_date else None,
            'preferred_time': self.preferred_time,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'contacted_at': self.contacted_at.isoformat() if self.contacted_at else None,
            'notes': self.notes
        }

class AdminSettings(db.Model):
    """Admin settings for chart zoom ranges and other configurations"""
    __tablename__ = 'admin_settings'
    
    setting_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    setting_type = db.Column(db.String(50), default='string')  # string, number, json, boolean
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationship to user
    creator = db.relationship('User', backref='created_settings')
    
    def __repr__(self):
        return f'<AdminSetting {self.setting_key}: {self.setting_value}>'
    
    def to_dict(self):
        return {
            'setting_id': self.setting_id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'setting_type': self.setting_type,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_setting(key, default_value=None):
        """Get a setting value by key"""
        setting = AdminSettings.query.filter_by(setting_key=key).first()
        if setting:
            # Convert based on type
            if setting.setting_type == 'number':
                try:
                    return float(setting.setting_value)
                except ValueError:
                    return default_value
            elif setting.setting_type == 'boolean':
                return setting.setting_value.lower() in ['true', '1', 'yes']
            elif setting.setting_type == 'json':
                try:
                    import json
                    return json.loads(setting.setting_value)
                except (ValueError, json.JSONDecodeError):
                    return default_value
            else:
                return setting.setting_value
        return default_value
    
    @staticmethod
    def set_setting(key, value, setting_type='string', description=None, created_by=None):
        """Set or update a setting"""
        setting = AdminSettings.query.filter_by(setting_key=key).first()
        
        # Convert value to string for storage
        if setting_type == 'json':
            import json
            value_str = json.dumps(value)
        elif setting_type == 'boolean':
            value_str = str(bool(value)).lower()
        else:
            value_str = str(value)
        
        if setting:
            # Update existing
            setting.setting_value = value_str
            setting.setting_type = setting_type
            if description:
                setting.description = description
            setting.updated_at = db.func.current_timestamp()
        else:
            # Create new
            setting = AdminSettings(
                setting_key=key,
                setting_value=value_str,
                setting_type=setting_type,
                description=description,
                created_by=created_by
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting