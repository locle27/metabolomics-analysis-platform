"""
Optimized PostgreSQL Models with Eager Loading
Fixes N+1 query problems that caused original performance issues
"""

import os
import json
from functools import lru_cache
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func, text
import time

# SQLAlchemy instance
db = SQLAlchemy()

class LipidClass(db.Model):
    __tablename__ = 'lipid_classes'
    
    class_id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationship to lipids
    lipids = db.relationship('MainLipid', back_populates='lipid_class', lazy='select')
    
    def to_dict(self):
        return {
            'class_id': self.class_id,
            'class_name': self.class_name,
            'description': self.description
        }

class MainLipid(db.Model):
    __tablename__ = 'main_lipids'
    
    lipid_id = db.Column(db.Integer, primary_key=True)
    lipid_name = db.Column(db.String(200), nullable=False)
    api_code = db.Column(db.String(100))
    class_id = db.Column(db.Integer, db.ForeignKey('lipid_classes.class_id'))
    retention_time = db.Column(db.Float)
    precursor_ion = db.Column(db.Float)
    product_ion = db.Column(db.Float)
    collision_energy = db.Column(db.Float)
    polarity = db.Column(db.String(10))
    xic_data = db.Column(db.JSON)
    extraction_success = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Optimized relationships with proper loading strategies
    lipid_class = db.relationship('LipidClass', back_populates='lipids', lazy='select')
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
    ion_lipid_name = db.Column(db.String(200))
    ion_lipidcode = db.Column(db.String(100))
    annotation_type = db.Column(db.String(50))
    retention_time = db.Column(db.Float)
    precursor_ion = db.Column(db.Float)
    product_ion = db.Column(db.Float)
    collision_energy = db.Column(db.Float)
    polarity = db.Column(db.String(10))
    int_start = db.Column(db.Float)
    int_end = db.Column(db.Float)
    integration_area = db.Column(db.Float)
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
            'int_start': self.int_start,
            'int_end': self.int_end,
            'integration_area': self.integration_area,
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
        
        # Single optimized query with all related data
        lipids = MainLipid.query.options(
            joinedload(MainLipid.lipid_class),          # JOIN to get class
            selectinload(MainLipid.annotated_ions)      # Separate optimized query for ions
        ).filter_by(extraction_success=True).all()
        
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
                'class_name': lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown',
                'annotated_ions_count': len(lipid.annotated_ions)  # No additional query!
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
        ).outerjoin(MainLipid).filter(
            MainLipid.extraction_success == True
        ).group_by(
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
        # Efficient COUNT queries
        total_lipids = MainLipid.query.filter_by(extraction_success=True).count()
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