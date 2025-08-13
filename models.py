"""
Metabolomics Flask App - SQLAlchemy Models
Optimized PostgreSQL Schema for Lipid and Annotated Ions Data
"""

from datetime import datetime
from typing import Optional, List
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, Boolean, DECIMAL, DateTime, Float
from sqlalchemy import ForeignKey, CheckConstraint, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

db = SQLAlchemy()

# =====================================================
# LIPID_CLASSES TABLE - Master lipid classification
# =====================================================
class LipidClass(db.Model):
    __tablename__ = 'lipid_classes'
    
    class_id = Column(Integer, primary_key=True, autoincrement=True)
    class_name = Column(String(50), nullable=False, unique=True, index=True)
    class_description = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    main_lipids = relationship("MainLipid", back_populates="lipid_class")
    
    def __repr__(self):
        return f"<LipidClass {self.class_id}: {self.class_name}>"
    
    def to_dict(self):
        return {
            'class_id': self.class_id,
            'class_name': self.class_name,
            'class_description': self.class_description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

# =====================================================
# MAIN_LIPIDS TABLE - Core lipid entities (823 lipids)
# =====================================================
class MainLipid(db.Model):
    __tablename__ = 'main_lipids'
    
    # Primary identification
    lipid_id = Column(Integer, primary_key=True, autoincrement=True)
    lipid_name = Column(String(255), nullable=False, unique=True, index=True)
    api_code = Column(String(100), nullable=False, unique=True, index=True)
    
    # Classification
    class_id = Column(Integer, ForeignKey('lipid_classes.class_id'), nullable=False, index=True)
    
    # Core properties
    precursor_ion = Column(String(50))
    product_ion = Column(String(50))
    retention_time = Column(Float, index=True)
    collision_energy = Column(Integer)
    polarity = Column(String(20), default='Positive')
    internal_standard = Column(String(255))
    
    # XIC data stored as JSONB for performance
    xic_data = Column(JSON)  # Stores array of {time, intensity} points
    
    # Extraction metadata
    extraction_timestamp = Column(DateTime, default=func.current_timestamp())
    extraction_method = Column(String(100))
    extraction_success = Column(Boolean, default=True, index=True)
    
    # Audit fields
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    lipid_class = relationship("LipidClass", back_populates="main_lipids")
    annotated_ions = relationship("AnnotatedIon", back_populates="main_lipid", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("polarity IN ('Positive', 'Negative')", name='chk_valid_polarity'),
        CheckConstraint("retention_time >= 0", name='chk_positive_rt'),
        CheckConstraint("collision_energy >= 0", name='chk_positive_ce'),
        Index('ix_main_lipids_class_rt', 'class_id', 'retention_time'),  # Composite index for filtering
    )
    
    @hybrid_property
    def has_multiple_annotations(self):
        """Check if lipid has multiple annotated ions."""
        return len(self.annotated_ions) > 1
    
    @hybrid_property
    def xic_peak_intensity(self):
        """Get maximum intensity from XIC data."""
        if self.xic_data and isinstance(self.xic_data, list):
            intensities = [point.get('intensity', 0) for point in self.xic_data if isinstance(point, dict)]
            return max(intensities) if intensities else 0
        return 0
    
    def __repr__(self):
        return f"<MainLipid {self.lipid_id}: {self.lipid_name}>"
    
    def to_dict(self, include_xic=False):
        result = {
            'lipid_id': self.lipid_id,
            'lipid_name': self.lipid_name,
            'api_code': self.api_code,
            'class_name': self.lipid_class.class_name if self.lipid_class else None,
            'precursor_ion': self.precursor_ion,
            'product_ion': self.product_ion,
            'retention_time': self.retention_time,
            'collision_energy': self.collision_energy,
            'polarity': self.polarity,
            'internal_standard': self.internal_standard,
            'annotated_ions_count': len(self.annotated_ions),
            'has_multiple_annotations': self.has_multiple_annotations,
            'xic_peak_intensity': self.xic_peak_intensity,
            'extraction_success': self.extraction_success,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
        
        if include_xic and self.xic_data:
            result['xic_data'] = self.xic_data
            
        return result

# =====================================================
# ANNOTATED_IONS TABLE - All annotated ions with parent relationships
# =====================================================
class AnnotatedIon(db.Model):
    __tablename__ = 'annotated_ions'
    
    # Primary identification
    ion_id = Column(Integer, primary_key=True, autoincrement=True)
    main_lipid_id = Column(Integer, ForeignKey('main_lipids.lipid_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Ion properties
    ion_lipid_name = Column(String(255), nullable=False, index=True)
    ion_lipidcode = Column(String(100), index=True)
    annotation_type = Column(String(100), index=True)  # 'Current lipid', '+2 isotope', 'Similar MRM', etc.
    
    # Mass spectrometry data
    precursor_ion = Column(String(50))
    product_ion = Column(String(50))
    retention_time = Column(Float, index=True)
    collision_energy = Column(Integer)
    polarity = Column(String(20))
    response_factor = Column(Float, default=1.0)
    
    # Integration windows
    int_start = Column(Float)
    int_end = Column(Float)
    
    # Flags
    is_main_lipid = Column(Boolean, default=False, index=True)  # True for the primary lipid
    
    # Audit fields
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    main_lipid = relationship("MainLipid", back_populates="annotated_ions")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("retention_time >= 0", name='chk_ion_positive_rt'),
        CheckConstraint("response_factor > 0", name='chk_positive_response_factor'),
        Index('ix_annotated_ions_main_type', 'main_lipid_id', 'annotation_type'),
        Index('ix_annotated_ions_rt_range', 'retention_time'),
    )
    
    def __repr__(self):
        return f"<AnnotatedIon {self.ion_id}: {self.ion_lipid_name}>"
    
    def to_dict(self):
        return {
            'ion_id': self.ion_id,
            'main_lipid_id': self.main_lipid_id,
            'main_lipid_name': self.main_lipid.lipid_name if self.main_lipid else None,
            'ion_lipid_name': self.ion_lipid_name,
            'ion_lipidcode': self.ion_lipidcode,
            'annotation_type': self.annotation_type,
            'precursor_ion': self.precursor_ion,
            'product_ion': self.product_ion,
            'retention_time': self.retention_time,
            'collision_energy': self.collision_energy,
            'polarity': self.polarity,
            'response_factor': self.response_factor,
            'int_start': self.int_start,
            'int_end': self.int_end,
            'is_main_lipid': self.is_main_lipid,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

# =====================================================
# CHART_SESSIONS TABLE - Track user chart generation sessions
# =====================================================
class ChartSession(db.Model):
    __tablename__ = 'chart_sessions'
    
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    main_lipid_id = Column(Integer, ForeignKey('main_lipids.lipid_id'), nullable=False, index=True)
    
    # Chart parameters
    selected_ions = Column(JSON)  # Array of selected annotated ion IDs
    rt_window_min = Column(Float, default=0.6)  # RT window for focused chart
    chart_type = Column(String(50), default='dual')  # 'dual', 'focused', 'overview'
    
    # Session metadata
    user_ip = Column(String(45))
    session_timestamp = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    main_lipid = relationship("MainLipid")
    
    def __repr__(self):
        return f"<ChartSession {self.session_id}: {self.main_lipid.lipid_name if self.main_lipid else 'Unknown'}>"
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'main_lipid_id': self.main_lipid_id,
            'main_lipid_name': self.main_lipid.lipid_name if self.main_lipid else None,
            'selected_ions': self.selected_ions,
            'rt_window_min': self.rt_window_min,
            'chart_type': self.chart_type,
            'session_timestamp': self.session_timestamp.isoformat() if self.session_timestamp else None
        }

# =====================================================
# DATABASE UTILITY FUNCTIONS
# =====================================================

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)

def create_all_tables(app):
    """Create all tables"""
    with app.app_context():
        db.create_all()
        print("All metabolomics tables created successfully!")

def get_db_stats(app):
    """Get database statistics"""
    with app.app_context():
        stats = {}
        stats['lipid_classes'] = LipidClass.query.count()
        stats['main_lipids'] = MainLipid.query.count()
        stats['successful_extractions'] = MainLipid.query.filter_by(extraction_success=True).count()
        stats['annotated_ions'] = AnnotatedIon.query.count()
        stats['multi_ion_lipids'] = db.session.query(MainLipid.lipid_id).join(AnnotatedIon).group_by(MainLipid.lipid_id).having(func.count(AnnotatedIon.ion_id) > 1).count()
        stats['chart_sessions'] = ChartSession.query.count()
        return stats

# =====================================================
# SAMPLE DATA FUNCTIONS
# =====================================================

def create_sample_lipid_classes(app):
    """Create sample lipid classes"""
    with app.app_context():
        # Clear existing data
        db.session.query(ChartSession).delete()
        db.session.query(AnnotatedIon).delete()
        db.session.query(MainLipid).delete()
        db.session.query(LipidClass).delete()
        
        # Create common lipid classes
        classes = [
            LipidClass(class_name="AC", class_description="Acylcarnitines"),
            LipidClass(class_name="TG", class_description="Triacylglycerols"),
            LipidClass(class_name="PC", class_description="Phosphatidylcholines"),
            LipidClass(class_name="PE", class_description="Phosphatidylethanolamines"),
            LipidClass(class_name="SM", class_description="Sphingomyelins"),
            LipidClass(class_name="Cer", class_description="Ceramides"),
            LipidClass(class_name="LPC", class_description="Lysophosphatidylcholines"),
            LipidClass(class_name="LPE", class_description="Lysophosphatidylethanolamines"),
        ]
        
        db.session.add_all(classes)
        db.session.commit()
        
        print("Sample lipid classes created successfully!")
        return len(classes)

# =====================================================
# QUERY HELPER FUNCTIONS
# =====================================================

def get_lipids_by_class(class_name: str, limit: int = None):
    """Get lipids filtered by class"""
    query = MainLipid.query.join(LipidClass).filter(LipidClass.class_name == class_name)
    if limit:
        query = query.limit(limit)
    return query.all()

def get_lipids_by_rt_range(min_rt: float, max_rt: float):
    """Get lipids within retention time range"""
    return MainLipid.query.filter(
        MainLipid.retention_time >= min_rt,
        MainLipid.retention_time <= max_rt
    ).all()

def get_multi_ion_lipids(limit: int = None):
    """Get lipids with multiple annotated ions"""
    query = MainLipid.query.join(AnnotatedIon).group_by(MainLipid.lipid_id).having(func.count(AnnotatedIon.ion_id) > 1)
    if limit:
        query = query.limit(limit)
    return query.all()

def search_lipids(search_term: str):
    """Search lipids by name"""
    return MainLipid.query.filter(
        MainLipid.lipid_name.ilike(f'%{search_term}%')
    ).all()