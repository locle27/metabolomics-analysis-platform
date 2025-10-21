#!/usr/bin/env python3
"""
Update CompoundIndex database with correct ISTD mappings from Second List Lipidomic.xlsx
This is the authoritative ISTD reference for ALZ format files.
"""

from app import app, db
from models import CompoundIndex
import pandas as pd
import sys

def update_istd_mappings():
    """Update CompoundIndex with correct ISTDs from Second List Lipidomic.xlsx"""

    alz_istd_file = '/mnt/c/Users/T14/Desktop/metabolomics-project/Second List Lipidomic.xlsx'

    print("=" * 80)
    print("UPDATING CompoundIndex WITH CORRECT ALZ ISTD MAPPINGS")
    print("=" * 80)
    print(f"\nSource: {alz_istd_file}")
    print()

    # Read the correct ISTD mappings
    try:
        df = pd.read_excel(alz_istd_file)
        print(f"✅ Loaded {len(df)} substance → ISTD mappings")
    except Exception as e:
        print(f"❌ Failed to read Excel file: {e}")
        return False

    with app.app_context():
        updates = 0
        mismatches_fixed = 0
        not_found = []

        for idx, row in df.iterrows():
            substance = row['Name']
            correct_istd = row['IS']

            # Skip rows with no ISTD
            if pd.isna(correct_istd):
                continue

            # Find in database
            comp = CompoundIndex.query.filter_by(compound=substance).first()

            if comp:
                old_istd = comp.istd

                # Normalize both for comparison (strip whitespace)
                old_istd_normalized = old_istd.strip() if old_istd else None
                new_istd_normalized = correct_istd.strip()

                if old_istd_normalized != new_istd_normalized:
                    print(f"🔄 Updating: {substance}")
                    print(f"   Old ISTD: {old_istd}")
                    print(f"   New ISTD: {correct_istd}")

                    comp.istd = correct_istd  # Update with correct ISTD
                    mismatches_fixed += 1

                updates += 1
            else:
                not_found.append(substance)

        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Database updated successfully!")
            print(f"   Total substances processed: {updates}")
            print(f"   ISTDs corrected: {mismatches_fixed}")

            if not_found:
                print(f"\n⚠️  Substances not found in database: {len(not_found)}")
                for substance in not_found[:10]:
                    print(f"   - {substance}")
                if len(not_found) > 10:
                    print(f"   ... and {len(not_found) - 10} more")

            return True

        except Exception as e:
            print(f"\n❌ Failed to commit changes: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("\n🚀 Starting ISTD mapping update...")
    print("   This will update CompoundIndex with correct ALZ format ISTDs\n")

    success = update_istd_mappings()

    if success:
        print("\n" + "=" * 80)
        print("✅ UPDATE COMPLETE")
        print("=" * 80)
        print("\nThe CompoundIndex database now has correct ISTD mappings")
        print("from 'Second List Lipidomic.xlsx' for ALZ format files.")
        print("\nNext steps:")
        print("1. Test with 40sample ALZ.xlsx")
        print("2. Click on different substance types (CE, Cer, PC, PE)")
        print("3. Verify each shows its correct ISTD in the modal")
        print()
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ UPDATE FAILED")
        print("=" * 80)
        sys.exit(1)
