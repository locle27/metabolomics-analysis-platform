#!/usr/bin/env python3

"""
Create reference data tables in the production database and import data
"""

import os
from flask import Flask
from models import db, SampleIndex, CompoundIndex
import pandas as pd

def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    
    # Use the same database configuration as the main app
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables")
        return None
    
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev-key'
    
    db.init_app(app)
    print(f"✅ Connected to database: {DATABASE_URL[:50]}...")
    return app

def create_tables_and_import():
    """Create tables and import reference data"""
    app = create_app()
    if not app:
        return False
    
    with app.app_context():
        try:
            # Create all tables (this will create the new reference tables)
            print("🔧 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Check if tables are empty (need import)
            sample_count = SampleIndex.query.count()
            compound_count = CompoundIndex.query.count()
            
            print(f"📊 Current data: {sample_count} samples, {compound_count} compounds")
            
            if sample_count == 0 or compound_count == 0:
                print("📁 Importing reference data from Excel...")
                import_reference_data()
            else:
                print("✅ Reference data already exists")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

def import_reference_data():
    """Import reference data from Excel file"""
    file_path = 'Calculate alysis.xlsx'
    
    if not os.path.exists(file_path):
        print(f"❌ Excel file not found: {file_path}")
        return False
    
    try:
        # Import Sample Index
        print("📊 Importing Sample Index...")
        df_samples = pd.read_excel(file_path, sheet_name='Sample index')
        
        # Clear existing data
        SampleIndex.query.delete()
        
        for _, row in df_samples.iterrows():
            sample_record = SampleIndex(
                sample=str(row['sample']).strip(),
                paired_nist=str(row['paired_nist']).strip()
            )
            db.session.add(sample_record)
        
        print(f"✅ Imported {len(df_samples)} sample index records")
        
        # Import Compound Index
        print("🧪 Importing Compound Index...")
        df_compounds = pd.read_excel(file_path, sheet_name='Compound index')
        
        # Clear existing data
        CompoundIndex.query.delete()
        
        for _, row in df_compounds.iterrows():
            compound_record = CompoundIndex(
                compound=str(row['Compound']).strip(),
                istd=str(row['ISTD']).strip(),
                conc_nm=float(row['Conc. (nM)']) if pd.notna(row['Conc. (nM)']) else None,
                response_factor=float(row['Response factor']) if pd.notna(row['Response factor']) else 1.0,
                nist_conc_nm=float(row['NIST Conc. (nM)']) if pd.notna(row['NIST Conc. (nM)']) else None
            )
            db.session.add(compound_record)
        
        print(f"✅ Imported {len(df_compounds)} compound index records")
        
        # Commit all changes
        db.session.commit()
        
        # Verify import
        final_sample_count = SampleIndex.query.count()
        final_compound_count = CompoundIndex.query.count()
        
        print(f"🎉 IMPORT COMPLETE!")
        print(f"📊 Final counts: {final_sample_count} samples, {final_compound_count} compounds")
        
        # Show sample data
        samples = SampleIndex.query.limit(3).all()
        compounds = CompoundIndex.query.limit(3).all()
        
        print("📋 Sample data preview:")
        for sample in samples:
            print(f"  {sample.sample} → {sample.paired_nist}")
        
        print("🧪 Compound data preview:")
        for compound in compounds:
            print(f"  {compound.compound} | ISTD: {compound.istd} | RF: {compound.response_factor}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    print("🚀 CREATING REFERENCE TABLES IN PRODUCTION DATABASE")
    print("=" * 60)
    
    success = create_tables_and_import()
    
    if success:
        print("\n✅ SUCCESS: Reference tables created and data imported")
        print("🎯 The calculation tool should now work correctly")
    else:
        print("\n❌ FAILED: Could not create tables or import data")
        print("🔧 Check database connection and file paths")