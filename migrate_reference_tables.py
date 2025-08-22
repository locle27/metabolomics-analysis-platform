#!/usr/bin/env python3

"""
Create reference tables by running the Flask app initialization
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_tables():
    """Create reference tables using Flask app context"""
    try:
        # Import app components
        from app import app, db
        from models import SampleIndex, CompoundIndex
        import pandas as pd
        
        print("🔗 Using Flask app database connection...")
        
        with app.app_context():
            print("🔧 Creating reference tables...")
            
            # Create all tables (this will add the new reference tables)
            db.create_all()
            print("✅ Database tables created/verified")
            
            # Check current data
            try:
                sample_count = SampleIndex.query.count()
                compound_count = CompoundIndex.query.count()
                print(f"📊 Current data: {sample_count} samples, {compound_count} compounds")
            except Exception as e:
                print(f"📊 Tables are new, proceeding with import... ({e})")
                sample_count = 0
                compound_count = 0
            
            # Import data if tables are empty
            if sample_count == 0 or compound_count == 0:
                print("📁 Importing reference data...")
                
                file_path = 'Calculate alysis.xlsx'
                if not os.path.exists(file_path):
                    print(f"❌ Excel file not found: {file_path}")
                    return False
                
                # Import Sample Index
                print("📊 Reading Sample Index sheet...")
                df_samples = pd.read_excel(file_path, sheet_name='Sample index')
                print(f"Found {len(df_samples)} sample records")
                
                # Clear and import samples
                SampleIndex.query.delete()
                for _, row in df_samples.iterrows():
                    sample_record = SampleIndex(
                        sample=str(row['sample']).strip(),
                        paired_nist=str(row['paired_nist']).strip()
                    )
                    db.session.add(sample_record)
                
                # Import Compound Index
                print("🧪 Reading Compound Index sheet...")
                df_compounds = pd.read_excel(file_path, sheet_name='Compound index')
                print(f"Found {len(df_compounds)} compound records")
                
                # Clear and import compounds
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
                
                # Commit changes
                db.session.commit()
                print("✅ Data import committed to database")
                
                # Verify final counts
                final_sample_count = SampleIndex.query.count()
                final_compound_count = CompoundIndex.query.count()
                
                print(f"🎉 IMPORT COMPLETE!")
                print(f"📊 Final counts: {final_sample_count} samples, {final_compound_count} compounds")
                
                # Show preview
                samples = SampleIndex.query.limit(3).all()
                compounds = CompoundIndex.query.limit(3).all()
                
                print("📋 Sample data preview:")
                for sample in samples:
                    print(f"  {sample.sample} → {sample.paired_nist}")
                
                print("🧪 Compound data preview:")
                for compound in compounds:
                    print(f"  {compound.compound} | ISTD: {compound.istd}")
                
            else:
                print("✅ Reference data already exists, no import needed")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 MIGRATING REFERENCE TABLES")
    print("=" * 50)
    
    success = migrate_tables()
    
    if success:
        print("\n✅ SUCCESS: Reference tables are ready!")
        print("🎯 The calculation tool should now work with database reference data")
    else:
        print("\n❌ FAILED: Migration encountered errors")
        print("🔧 Check the error details above")