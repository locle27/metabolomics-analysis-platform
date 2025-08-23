#!/usr/bin/env python3

"""
Extract the exact NIST reference values from the original file
"""

import pandas as pd

def get_nist_reference_values():
    """Extract NIST reference values for proper calculation"""
    print("🎯 EXTRACTING NIST REFERENCE VALUES")
    print("=" * 50)
    
    # Read the original file
    original_file = 'Calculate_alysis.xlsx'
    original_data = pd.read_excel(original_file, sheet_name='Ratio')
    
    # Find the NIST reference row
    nist_ref_row = None
    for idx, row in original_data.iterrows():
        compound = str(row.iloc[0]).strip().upper()
        if 'NIST' in compound and ('100' in compound or '1-100' in compound):
            nist_ref_row = idx
            print(f"Found NIST reference row at index {idx}: {row.iloc[0]}")
            break
    
    if nist_ref_row is not None:
        nist_reference_data = original_data.iloc[nist_ref_row]
        
        # Get NIST columns
        nist_cols = [col for col in original_data.columns if 'NIST' in str(col).upper()]
        
        print(f"\n🎯 NIST REFERENCE VALUES:")
        for nist_col in nist_cols:
            value = nist_reference_data[nist_col]
            print(f"  {nist_col}: {value}")
        
        # Test calculation with first compound
        first_compound = original_data.iloc[0]
        sample_cols = [col for col in original_data.columns if 'PH-HC_' in str(col)][:3]
        
        print(f"\n🧮 TEST CALCULATION (First compound: {first_compound.iloc[0]}):")
        
        for i, sample_col in enumerate(sample_cols):
            ratio_value = first_compound[sample_col]
            
            # Determine which NIST column to use based on sample
            # PH-HC_5601-5625 should use NIST_1-100 (1)
            # PH-HC_5626-5650 should use NIST_1-100 (2)
            # etc.
            
            sample_num = int(sample_col.split('_')[1])
            if sample_num <= 5625:
                nist_col_to_use = 'NIST_1-100 (1)'
            elif sample_num <= 5650:
                nist_col_to_use = 'NIST_1-100 (2)'
            elif sample_num <= 5675:
                nist_col_to_use = 'NIST_1-100 (3)'
            else:
                nist_col_to_use = 'NIST_1-100 (4)'
            
            nist_ref_value = nist_reference_data[nist_col_to_use]
            calculated_nist = ratio_value / nist_ref_value
            
            print(f"  {sample_col}:")
            print(f"    Ratio: {ratio_value}")
            print(f"    NIST ref ({nist_col_to_use}): {nist_ref_value}")
            print(f"    Calculated NIST: {calculated_nist}")
        
        # Compare with original NIST results
        print(f"\n✅ COMPARING WITH ORIGINAL NIST RESULTS:")
        original_nist = pd.read_excel(original_file, sheet_name='NIST')
        first_nist_row = original_nist.iloc[0]
        
        for sample_col in sample_cols:
            expected_result = first_nist_row[sample_col]
            print(f"  {sample_col} expected: {expected_result}")

if __name__ == "__main__":
    get_nist_reference_values()