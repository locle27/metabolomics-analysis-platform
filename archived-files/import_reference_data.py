#!/usr/bin/env python3

"""
Import Sample Index and Compound Index reference data from Excel to database
This script loads the fixed reference data that will be used for all future calculations
"""

import pandas as pd
import sys
import os
from flask import Flask
from models import db, SampleIndex, CompoundIndex

def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///metabolomics.db')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev-key'
    
    db.init_app(app)
    return app

def import_sample_index_data(file_path):
    """Import Sample Index data from Excel file"""
    print("📊 Reading Sample Index data from Excel...")
    
    df = pd.read_excel(file_path, sheet_name='Sample index')
    print(f"Found {len(df)} sample index records")
    
    # Clear existing data
    print("🗑️ Clearing existing Sample Index data...")
    SampleIndex.query.delete()
    db.session.commit()
    
    # Import new data
    imported_count = 0
    for _, row in df.iterrows():
        sample_record = SampleIndex(
            sample=str(row['sample']).strip(),
            paired_nist=str(row['paired_nist']).strip()
        )
        db.session.add(sample_record)
        imported_count += 1
    
    db.session.commit()
    print(f"✅ Imported {imported_count} Sample Index records")
    
    # Verify import
    total_samples = SampleIndex.query.count()
    print(f"🔍 Verification: {total_samples} sample index records in database")
    
    return imported_count

def import_compound_index_data(file_path):
    """Import Compound Index data from Excel file"""
    print("📊 Reading Compound Index data from Excel...")
    
    df = pd.read_excel(file_path, sheet_name='Compound index')
    print(f"Found {len(df)} compound index records")
    print(f"Columns: {list(df.columns)}")
    
    # Clear existing data
    print("🗑️ Clearing existing Compound Index data...")
    CompoundIndex.query.delete()
    db.session.commit()
    
    # Import new data
    imported_count = 0
    for _, row in df.iterrows():
        compound_record = CompoundIndex(
            compound=str(row['Compound']).strip(),
            istd=str(row['ISTD']).strip(),
            conc_nm=float(row['Conc. (nM)']) if pd.notna(row['Conc. (nM)']) else None,
            response_factor=float(row['Response factor']) if pd.notna(row['Response factor']) else 1.0,
            nist_conc_nm=float(row['NIST Conc. (nM)']) if pd.notna(row['NIST Conc. (nM)']) else None
        )
        db.session.add(compound_record)
        imported_count += 1
    
    db.session.commit()
    print(f"✅ Imported {imported_count} Compound Index records")
    
    # Verify import
    total_compounds = CompoundIndex.query.count()
    print(f"🔍 Verification: {total_compounds} compound index records in database")
    
    return imported_count

def main():
    """Main import function"""
    print("🚀 QUANTITATIVE ANALYSIS REFERENCE DATA IMPORT")
    print("=" * 60)
    
    file_path = 'Calculate alysis.xlsx'
    
    if not os.path.exists(file_path):
        print(f"❌ Error: Excel file not found: {file_path}")
        sys.exit(1)
    
    # Create Flask app and database tables
    app = create_app()
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        print("✅ Database tables created/verified")
        
        try:
            # Import Sample Index data
            sample_count = import_sample_index_data(file_path)
            
            # Import Compound Index data  
            compound_count = import_compound_index_data(file_path)
            
            print(f"\n🎉 IMPORT COMPLETE!")
            print(f"📊 Sample Index records: {sample_count}")
            print(f"🧪 Compound Index records: {compound_count}")
            print(f"\n✅ Reference data is now available for calculation tool")
            
            # Show sample data
            print(f"\n📋 Sample data preview:")
            samples = SampleIndex.query.limit(5).all()
            for sample in samples:
                print(f"  {sample.sample} → {sample.paired_nist}")
            
            compounds = CompoundIndex.query.limit(5).all()
            print(f"\n🧪 Compound data preview:")
            for compound in compounds:
                print(f"  {compound.compound} | ISTD: {compound.istd} | RF: {compound.response_factor}")
            
        except Exception as e:
            print(f"❌ Error during import: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    main()