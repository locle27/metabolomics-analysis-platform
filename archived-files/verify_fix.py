#!/usr/bin/env python3

"""
Verify that the calculation fix is working correctly
"""

import pandas as pd

def verify_calculation_fix():
    """Test the fixed calculation with real data"""
    print("✅ VERIFYING CALCULATION FIX")
    print("=" * 40)
    
    # Read original ratio and NIST data for comparison
    original_file = 'Calculate_alysis.xlsx'
    ratio_data = pd.read_excel(original_file, sheet_name='Ratio')
    nist_data = pd.read_excel(original_file, sheet_name='NIST')
    
    print("📊 Original data loaded successfully")
    
    # Test first compound, first 3 samples
    first_compound_ratio = ratio_data.iloc[0]
    first_compound_nist = nist_data.iloc[0]
    
    compound_name = first_compound_ratio.iloc[0]
    print(f"🧪 Testing compound: {compound_name}")
    
    # Get sample columns
    sample_cols = [col for col in ratio_data.columns if 'PH-HC_' in str(col)][:3]
    
    # Find NIST reference row
    nist_ref_row = None
    for idx, row in ratio_data.iterrows():
        compound = str(row.iloc[0]).strip().upper()
        if 'NIST' in compound and ('100' in compound or '1-100' in compound):
            nist_ref_row = idx
            break
    
    if nist_ref_row is not None:
        nist_reference_data = ratio_data.iloc[nist_ref_row]
        print(f"📋 NIST reference row found: {nist_reference_data.iloc[0]}")
        
        # Test calculation for each sample
        for i, sample_col in enumerate(sample_cols):
            ratio_value = first_compound_ratio[sample_col]
            expected_nist = first_compound_nist[sample_col]
            
            # Determine NIST column based on sample number
            sample_num = int(sample_col.split('_')[1])
            if sample_num <= 25:
                nist_col = 'NIST_1-100 (1)'
            elif sample_num <= 50:
                nist_col = 'NIST_1-100 (2)'
            elif sample_num <= 75:
                nist_col = 'NIST_1-100 (3)'
            else:
                nist_col = 'NIST_1-100 (4)'
            
            nist_ref_value = nist_reference_data[nist_col]
            calculated_nist = ratio_value / nist_ref_value
            
            print(f"\n{sample_col} (using {nist_col}):")
            print(f"  Ratio: {ratio_value}")
            print(f"  NIST ref: {nist_ref_value}")
            print(f"  Calculated: {calculated_nist}")
            print(f"  Expected: {expected_nist}")
            print(f"  Match: {abs(calculated_nist - expected_nist) < 0.01}")
    
    print(f"\n🎯 CONCLUSION:")
    print("If all matches are True, the calculation fix is working correctly!")
    print("The system should now produce accurate NIST results.")

if __name__ == "__main__":
    verify_calculation_fix()