#!/usr/bin/env python3

"""
Check Sample Index sheet to understand NIST column mapping
"""

import pandas as pd

# Read the Sample Index sheet
file_path = 'Calculate_alysis.xlsx'
print(f"📊 Reading Sample Index from: {file_path}")

try:
    sample_index = pd.read_excel(file_path, sheet_name='Sample index')
    print(f"✅ Loaded Sample Index sheet: {sample_index.shape}")
    
    print("\n📋 Sample Index columns:")
    print(sample_index.columns.tolist())
    
    print("\n📊 First 10 sample mappings:")
    for idx, row in sample_index.head(10).iterrows():
        print(f"  {row.iloc[0]} → {row.iloc[1]}")
    
    # Look for PH-HC_5601
    print("\n🔍 Looking for PH-HC_5601 mapping:")
    for idx, row in sample_index.iterrows():
        if 'PH-HC_5601' in str(row.iloc[0]):
            print(f"  Found: {row.iloc[0]} → {row.iloc[1]}")
            break
    
    # Look for PH-HC_1 to PH-HC_100 mappings
    print("\n🔍 Looking for PH-HC_1 to PH-HC_100 mappings:")
    for i in range(1, 101):
        sample_name = f"PH-HC_{i}"
        for idx, row in sample_index.iterrows():
            if str(row.iloc[0]).strip() == sample_name:
                print(f"  {row.iloc[0]} → {row.iloc[1]}")
                break
                
except Exception as e:
    print(f"❌ Error reading Sample Index: {e}")
    
# Also check the Compound Index sheet
print("\n\n📊 Reading Compound Index sheet:")
try:
    compound_index = pd.read_excel(file_path, sheet_name='Compound index')
    print(f"✅ Loaded Compound Index sheet: {compound_index.shape}")
    
    print("\n📋 Compound Index columns:")
    print(compound_index.columns.tolist())
    
    print("\n🔍 Looking for AcylCarnitine 12:0:")
    for idx, row in compound_index.iterrows():
        if 'AcylCarnitine 12:0' in str(row.iloc[0]) or 'Acylcarnitine 12:0' in str(row.iloc[0]):
            print(f"  Found compound: {row.iloc[0]}")
            print(f"  Full row data:")
            for col in compound_index.columns:
                print(f"    {col}: {row[col]}")
            break
            
except Exception as e:
    print(f"❌ Error reading Compound Index: {e}")