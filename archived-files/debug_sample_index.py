#!/usr/bin/env python3

"""
DEBUG SAMPLE INDEX SHEET
Check why the sample-to-NIST mapping is failing
"""

import pandas as pd
import os

def debug_sample_index():
    """Debug the Sample Index sheet to understand the mapping issue"""
    
    print("🔍 DEBUG SAMPLE INDEX SHEET")
    print("=" * 60)
    
    excel_file = 'Calculate_alysis.xlsx'
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        return
    
    try:
        # Load Sample Index sheet
        sample_index = pd.read_excel(excel_file, sheet_name='Sample index')
        
        print(f"📊 Sample Index Shape: {sample_index.shape}")
        print(f"📊 Columns: {list(sample_index.columns)}")
        print(f"📊 First 10 rows:")
        print(sample_index.head(10))
        print()
        
        # Check column content
        if len(sample_index.columns) >= 2:
            col1 = sample_index.columns[0]
            col2 = sample_index.columns[1]
            
            print(f"📊 Column 1 '{col1}' values:")
            for i in range(min(10, len(sample_index))):
                val = sample_index.iloc[i, 0]
                print(f"  [{i}] '{val}' (type: {type(val)})")
            
            print(f"\n📊 Column 2 '{col2}' values:")
            for i in range(min(10, len(sample_index))):
                val = sample_index.iloc[i, 1]
                print(f"  [{i}] '{val}' (type: {type(val)})")
        
        # Test sample mapping logic
        print(f"\n🧪 TESTING SAMPLE MAPPING LOGIC:")
        print("-" * 40)
        
        # Build mapping exactly like the preview script
        sample_nist_map = {}
        for _, row in sample_index.iterrows():
            sample = str(row.iloc[0]).strip()
            nist = str(row.iloc[1]).strip()
            sample_nist_map[sample] = nist
            
        print(f"✅ Built mapping for {len(sample_nist_map)} samples")
        
        # Test specific samples
        test_samples = ['PH-HC_5601', 'PH-HC_5602', 'PH-HC_5603', 'PH-HC_5625', 'PH-HC_5626']
        
        for test_sample in test_samples:
            mapped_nist = sample_nist_map.get(test_sample, None)
            print(f"  {test_sample} → {mapped_nist or 'NOT FOUND'}")
        
        # Show all unique NIST values
        print(f"\n📊 ALL UNIQUE NIST VALUES:")
        unique_nist = sample_index.iloc[:, 1].dropna().unique()
        for nist_val in unique_nist:
            print(f"  '{nist_val}'")
        
        # Check for pattern matching issues
        print(f"\n🔍 PATTERN MATCHING TEST:")
        print("Looking for samples that start with 'PH-HC_'...")
        
        matching_samples = []
        for _, row in sample_index.iterrows():
            sample = str(row.iloc[0]).strip()
            if sample.startswith('PH-HC_'):
                matching_samples.append(sample)
        
        print(f"Found {len(matching_samples)} matching samples:")
        for i, sample in enumerate(matching_samples[:10]):
            nist = sample_nist_map.get(sample, 'NOT FOUND')
            print(f"  {sample} → {nist}")
        
        if len(matching_samples) > 10:
            print(f"  ... and {len(matching_samples) - 10} more")
    
    except Exception as e:
        print(f"❌ Error debugging Sample Index: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_sample_index()