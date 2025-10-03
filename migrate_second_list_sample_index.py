#!/usr/bin/env python3
"""
Migration script to add sample index pattern for Second List Lipidomic
Pattern: 50 samples per 1 NIST standard
This allows other projects to reuse this sample pattern
"""

import pandas as pd
from app import app, db
from models import SampleIndex, CompoundIndex

def create_second_list_sample_index():
    """Create sample index for Second List Lipidomic (50 samples : 1 NIST)"""

    print("\n🔄 Creating Second List Lipidomic Sample Index Pattern...")
    print("=" * 70)

    # Define pattern: 50 samples per 1 NIST standard
    # Using prefix "SL_" (Second List) to differentiate from PH-HC_ samples
    sample_pattern = []

    # Generate 50 samples paired with NIST_SL (1)
    for i in range(1, 51):
        sample_pattern.append({
            'sample': f'SL_{i}',
            'paired_nist': 'NIST_SL (1)'
        })

    print(f"📊 Generated {len(sample_pattern)} sample entries")
    print(f"   Pattern: 50 samples → NIST_SL (1)")
    print(f"   Sample range: SL_1 to SL_50")

    # Check if pattern already exists
    existing = SampleIndex.query.filter(SampleIndex.sample.like('SL_%')).count()

    if existing > 0:
        print(f"\n⚠️  Found {existing} existing SL_ entries in database")
        response = input("Do you want to DELETE and RECREATE them? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Migration cancelled")
            return False

        # Delete existing SL_ entries
        deleted = SampleIndex.query.filter(SampleIndex.sample.like('SL_%')).delete()
        db.session.commit()
        print(f"🗑️  Deleted {deleted} existing entries")

    # Insert new pattern
    success_count = 0
    for entry in sample_pattern:
        try:
            sample_index = SampleIndex(
                sample=entry['sample'],
                paired_nist=entry['paired_nist']
            )
            db.session.add(sample_index)
            success_count += 1
        except Exception as e:
            print(f"❌ Error adding {entry['sample']}: {e}")
            db.session.rollback()
            return False

    try:
        db.session.commit()
        print(f"\n✅ Successfully inserted {success_count} sample index entries")

        # Verify
        total_sl = SampleIndex.query.filter(SampleIndex.sample.like('SL_%')).count()
        print(f"✅ Verification: {total_sl} SL_ entries now in database")

        return True

    except Exception as e:
        print(f"❌ Error committing to database: {e}")
        db.session.rollback()
        return False


def import_second_list_compounds():
    """Import compound mappings from Second List Lipidomic.xlsx"""

    print("\n🔄 Importing Second List Lipidomic Compound Mappings...")
    print("=" * 70)

    try:
        # Read the Excel file
        file_path = "/mnt/c/Users/T14/Desktop/metabolomics-project/Second List Lipidomic.xlsx"
        df = pd.read_excel(file_path)

        print(f"📁 Loaded file: {file_path}")
        print(f"📊 Found {len(df)} compounds")
        print(f"   Columns: {list(df.columns)}")

        # Validate columns
        if 'Name' not in df.columns or 'IS' not in df.columns:
            print("❌ Error: Expected columns 'Name' and 'IS' not found")
            return False

        # Check existing compounds
        existing_compounds = set(c.compound for c in CompoundIndex.query.all())
        new_count = 0
        duplicate_count = 0

        print("\n📝 Processing compounds...")

        for idx, row in df.iterrows():
            compound_name = str(row['Name']).strip()
            istd = str(row['IS']).strip()

            if compound_name in existing_compounds:
                duplicate_count += 1
                if duplicate_count <= 5:  # Show first 5 duplicates
                    print(f"   ⚠️  Duplicate: {compound_name} (already exists)")
                continue

            try:
                # Add new compound
                compound = CompoundIndex(
                    compound=compound_name,
                    istd=istd,
                    conc_nm=0.0  # Default concentration, can be updated later
                )
                db.session.add(compound)
                existing_compounds.add(compound_name)
                new_count += 1

                if new_count <= 10:  # Show first 10 additions
                    print(f"   ✅ Added: {compound_name} → ISTD: {istd}")

            except Exception as e:
                print(f"   ❌ Error adding {compound_name}: {e}")

        # Commit changes
        db.session.commit()

        print(f"\n✅ Successfully added {new_count} new compounds")
        if duplicate_count > 0:
            print(f"⚠️  Skipped {duplicate_count} duplicate compounds")

        # Verify
        total_compounds = CompoundIndex.query.count()
        print(f"✅ Total compounds in database: {total_compounds}")

        return True

    except Exception as e:
        print(f"❌ Error importing compounds: {e}")
        db.session.rollback()
        return False


def verify_migration():
    """Verify the migration was successful"""

    print("\n🔍 Verifying Migration...")
    print("=" * 70)

    # Check sample index
    sl_samples = SampleIndex.query.filter(SampleIndex.sample.like('SL_%')).all()
    print(f"✅ SL_ Sample Index Entries: {len(sl_samples)}")

    if len(sl_samples) > 0:
        print(f"   First: {sl_samples[0].sample} → {sl_samples[0].paired_nist}")
        print(f"   Last:  {sl_samples[-1].sample} → {sl_samples[-1].paired_nist}")

    # Check compound index
    total_compounds = CompoundIndex.query.count()
    print(f"✅ Total Compound Index Entries: {total_compounds}")

    # Show some Second List specific compounds (if identifiable)
    acyl_compounds = CompoundIndex.query.filter(
        CompoundIndex.compound.like('AcylCarnitine%')
    ).limit(5).all()

    if acyl_compounds:
        print(f"   Sample AcylCarnitine compounds:")
        for comp in acyl_compounds:
            print(f"   - {comp.compound} → ISTD: {comp.istd}")

    print("\n" + "=" * 70)
    print("✅ Migration verification complete!")


if __name__ == '__main__':
    with app.app_context():
        print("\n" + "=" * 70)
        print("🚀 SECOND LIST LIPIDOMIC MIGRATION")
        print("=" * 70)
        print("This will:")
        print("  1. Add 50 sample index entries (SL_1 to SL_50)")
        print("  2. Each sample paired with NIST_SL (1)")
        print("  3. Import compound mappings from Second List Lipidomic.xlsx")
        print("=" * 70)

        response = input("\nProceed with migration? (yes/no): ")

        if response.lower() == 'yes':
            # Step 1: Create sample index
            if create_second_list_sample_index():
                print("✅ Sample index migration complete")
            else:
                print("❌ Sample index migration failed")
                exit(1)

            # Step 2: Import compounds
            if import_second_list_compounds():
                print("✅ Compound import complete")
            else:
                print("❌ Compound import failed")
                exit(1)

            # Step 3: Verify
            verify_migration()

            print("\n🎉 Migration completed successfully!")
        else:
            print("❌ Migration cancelled")
