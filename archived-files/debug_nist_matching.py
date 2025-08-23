#!/usr/bin/env python3

"""
Debug NIST column matching issue
"""

import pandas as pd
import numpy as np

# Read the Excel file
file_path = 'Calculate_alysis.xlsx'
print(f"📊 Reading Excel file: {file_path}")

# Read the main data sheet
main_data = pd.read_excel(file_path, sheet_name='PH-HC_5601-5700')
print(f"✅ Loaded main data sheet: {main_data.shape}")

# Display column names
print("\n📋 All columns:")
for i, col in enumerate(main_data.columns):
    print(f"  [{i}] '{col}' (type: {type(col).__name__})")

# Find NIST columns
nist_columns = [col for col in main_data.columns if 'NIST' in str(col)]
print(f"\n🔍 Found {len(nist_columns)} NIST columns:")
for col in nist_columns:
    print(f"  - '{col}'")

# Check if header is numeric
print("\n🔢 Checking for numeric headers:")
numeric_headers = [col for col in main_data.columns if isinstance(col, (int, float))]
print(f"  Found {len(numeric_headers)} numeric headers")

# Skip header row if needed
skip_rows = 1  # Assuming first row is header
compounds = main_data.iloc[skip_rows:, 0].astype(str).str.strip()
area_data_values = main_data.iloc[skip_rows:, 1:]

print(f"\n📊 Data shape after skipping header:")
print(f"  Compounds: {len(compounds)}")
print(f"  Area data: {area_data_values.shape}")

# Look for AcylCarnitine 12:0
print("\n🔍 Looking for AcylCarnitine 12:0:")
for idx, compound in enumerate(compounds):
    if 'AcylCarnitine 12:0' in compound or 'Acylcarnitine 12:0' in compound:
        print(f"  Found at index {idx}: '{compound}'")
        
        # Check NIST values for this compound
        print(f"\n  NIST values for this compound:")
        for nist_col in nist_columns:
            try:
                value = area_data_values.iloc[idx][nist_col]
                print(f"    {nist_col}: {value}")
            except Exception as e:
                print(f"    {nist_col}: ERROR - {e}")
        break

# Test exact column matching
print("\n🧪 Testing column name matching:")
test_names = [
    "NIST_1-100 (1)",
    "NIST_1-100(1)",
    "NIST_1-100 (1) ",
    " NIST_1-100 (1)"
]

for test_name in test_names:
    print(f"\n  Testing: '{test_name}'")
    for col in nist_columns:
        if str(col).strip() == test_name:
            print(f"    ✅ MATCH with column: '{col}'")
        elif str(col) == test_name:
            print(f"    ✅ EXACT MATCH with column: '{col}'")

# Show actual NIST column values for compound at index 1 (AcylCarnitine 12:0)
print("\n📊 NIST values at index 1 (should be AcylCarnitine 12:0):")
if len(compounds) > 1:
    print(f"  Compound: {compounds.iloc[1]}")
    for col in nist_columns:
        try:
            value = area_data_values.iloc[1][col]
            print(f"  {col}: {value}")
        except Exception as e:
            print(f"  {col}: ERROR - {e}")