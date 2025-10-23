#!/usr/bin/env python3
"""
Fix ISTD mappings for PH-HC format compounds from compound-index.xlsx
"""

import pandas as pd
from app import app, db
from models import CompoundIndex

def fix_ph_hc_istd_mappings():
    """Update database with correct ISTD mappings from compound-index.xlsx"""

    compound_index_file = '/mnt/c/Users/T14/Desktop/metabolomics-project/compound-index.xlsx'

    print("🔄 Loading compound-index.xlsx...")
    df = pd.read_excel(compound_index_file)

    print(f"✅ Loaded {len(df)} compounds from compound-index.xlsx")
    print()

    with app.app_context():
        updates = 0
        mismatches_fixed = 0
        not_found = []

        print("🔍 Checking and updating ISTD mappings...")

        for idx, row in df.iterrows():
            compound_name = row['Compound']
            correct_istd = row['ISTD']

            # Strip " ISTD" suffix from ISTD values (compound-index.xlsx has this extra suffix)
            if isinstance(correct_istd, str) and correct_istd.endswith(' ISTD'):
                correct_istd = correct_istd[:-5]  # Remove last 5 characters " ISTD"

            # Query database
            db_compound = CompoundIndex.query.filter_by(compound=compound_name).first()

            if db_compound:
                # Check if ISTD matches
                if db_compound.istd != correct_istd:
                    print(f"❌ MISMATCH: {compound_name}")
                    print(f"   Database: {db_compound.istd}")
                    print(f"   Correct:  {correct_istd}")

                    # Update
                    db_compound.istd = correct_istd
                    mismatches_fixed += 1
                    print(f"   ✅ FIXED")
                    print()

                updates += 1
            else:
                not_found.append(compound_name)

        # Commit all changes
        db.session.commit()

        print()
        print("="*80)
        print(f"✅ ISTD mappings updated:")
        print(f"   Total compounds checked: {len(df)}")
        print(f"   Compounds updated: {updates}")
        print(f"   ISTDs corrected: {mismatches_fixed}")
        print(f"   Compounds not in database: {len(not_found)}")

        if not_found:
            print()
            print("⚠️ Compounds not found in database:")
            for comp in not_found[:10]:
                print(f"   - {comp}")
            if len(not_found) > 10:
                print(f"   ... and {len(not_found) - 10} more")

        print("="*80)

if __name__ == '__main__':
    fix_ph_hc_istd_mappings()
