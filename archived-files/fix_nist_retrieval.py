#!/usr/bin/env python3

"""
Fix NIST value retrieval issue
The problem: AcylCarnitine 12:0 should have NIST_1-100(1) = 0.0951
"""

import pandas as pd

# Read the Excel file
file_path = 'Calculate_alysis.xlsx'
print(f"📊 Reading Excel file: {file_path}")

# Read WITHOUT any header row to see raw data
main_data_raw = pd.read_excel(file_path, sheet_name='PH-HC_5601-5700', header=None)
print(f"✅ Loaded raw data (no header): {main_data_raw.shape}")

print("\n📋 First 5 rows, first 10 columns (RAW):")
print(main_data_raw.iloc[:5, :10])

# Now read with header
main_data = pd.read_excel(file_path, sheet_name='PH-HC_5601-5700')
print(f"\n✅ Loaded with header: {main_data.shape}")

# Find the NIST_1-100 (1) column
nist_target = None
print("\n🔍 Looking for NIST_1-100 (1) column:")
for col in main_data.columns:
    col_str = str(col)
    print(f"  Column: '{col_str}'")
    if 'NIST' in col_str and '1-100' in col_str and '(1)' in col_str:
        nist_target = col
        print(f"    ✅ Found target NIST column: '{col}'")
        break

if nist_target:
    # Get value for AcylCarnitine 12:0 (should be row 1 if we skip header)
    print(f"\n📊 Checking values in column '{nist_target}':")
    
    # First, let's see what's in the first few rows
    for i in range(min(5, len(main_data))):
        compound = main_data.iloc[i, 0]  # First column is compound
        nist_value = main_data.iloc[i][nist_target]
        print(f"  Row {i}: {compound} → {nist_value}")
        
        if 'AcylCarnitine 12:0' in str(compound):
            print(f"    🎯 This is AcylCarnitine 12:0! NIST value = {nist_value}")
            print(f"    Expected: 0.0951")
            if abs(float(nist_value) - 0.0951) < 0.0001:
                print(f"    ✅ Value matches expected!")
            else:
                print(f"    ❌ Value does NOT match expected!")

# Double-check by looking at raw positions
print("\n\n🔍 Double-checking with raw positions:")
print("Looking at position [2, CX] (Row 3, Column CX in Excel):")

# Find column index for NIST_1-100 (1) in raw data
for col_idx, col_value in enumerate(main_data_raw.iloc[0]):  # First row has headers
    if 'NIST' in str(col_value) and '1-100' in str(col_value) and '(1)' in str(col_value):
        print(f"  Found NIST_1-100 (1) at column index: {col_idx}")
        print(f"  Column header: '{col_value}'")
        
        # Get value at row 2 (3rd row in Excel, which is AcylCarnitine 12:0)
        value_at_row_2 = main_data_raw.iloc[2, col_idx]
        print(f"  Value at row 2 (AcylCarnitine 12:0): {value_at_row_2}")
        
        # Also show surrounding values for context
        print(f"\n  Context (rows 1-3):")
        for r in range(1, 4):
            compound = main_data_raw.iloc[r, 0]
            value = main_data_raw.iloc[r, col_idx]
            print(f"    Row {r}: {compound} → {value}")