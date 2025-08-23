#!/usr/bin/env python3

"""
Analyze the NIST calculation issue by comparing methodologies
"""

import pandas as pd
import sys
import os

def analyze_nist_issue():
    """Identify the specific NIST calculation problem"""
    print("🔍 ANALYZING NIST CALCULATION ISSUE")
    print("=" * 50)
    
    original_file = 'Calculate_alysis.xlsx'
    uploaded_file = 'Book1.xlsx'
    
    try:
        # Read original file sheets
        print("📊 Reading original Calculate_alysis.xlsx...")
        original_data = pd.read_excel(original_file, sheet_name=None)
        
        # Read uploaded file
        print("📊 Reading uploaded Book1.xlsx...")
        uploaded_data = pd.read_excel(uploaded_file, sheet_name=None)
        
        # Key sheets from original
        original_ph_sheet = original_data['PH-HC_5601-5700']
        original_ratio_sheet = original_data['Ratio'] 
        original_nist_sheet = original_data['NIST']
        
        # Uploaded sheet (should match PH-HC_5601-5700)
        uploaded_sheet = uploaded_data[list(uploaded_data.keys())[0]]
        
        print(f"\n🔍 ORIGINAL vs UPLOADED DATA COMPARISON:")
        print(f"Original PH-HC sheet: {original_ph_sheet.shape}")
        print(f"Uploaded sheet: {uploaded_sheet.shape}")
        
        # Compare first few rows to verify it's the same data
        print(f"\n📋 FIRST 3 COMPOUNDS COMPARISON:")
        
        # Handle header rows properly
        orig_start_row = 1 if str(original_ph_sheet.iloc[0, 0]).lower() == 'name' else 0
        upload_start_row = 1 if str(uploaded_sheet.iloc[0, 0]).lower() == 'name' else 0
        
        for i in range(3):
            orig_compound = original_ph_sheet.iloc[orig_start_row + i, 0]
            upload_compound = uploaded_sheet.iloc[upload_start_row + i, 0]
            print(f"  Row {i+1}: Original='{orig_compound}' | Uploaded='{upload_compound}'")
            
            # Compare first sample area
            orig_area = original_ph_sheet.iloc[orig_start_row + i, 1]
            upload_area = uploaded_sheet.iloc[upload_start_row + i, 1]
            print(f"    Areas: Original={orig_area} | Uploaded={upload_area}")
        
        print(f"\n🎯 ANALYZING ORIGINAL NIST CALCULATION METHOD:")
        
        # Get the first compound from ratio sheet
        first_compound = original_ratio_sheet.iloc[0, 0]
        print(f"First compound in ratio sheet: {first_compound}")
        
        # Get ratio values for first few samples
        sample_cols = [col for col in original_ratio_sheet.columns if 'PH-HC_' in str(col)][:3]
        print(f"Sample columns: {sample_cols}")
        
        # Get NIST reference columns
        nist_cols = [col for col in original_ratio_sheet.columns if 'NIST' in str(col).upper()]
        print(f"NIST columns: {nist_cols}")
        
        # Find NIST reference row
        nist_ref_row = None
        for idx, row in original_ratio_sheet.iterrows():
            compound = str(row.iloc[0]).strip().upper()
            if 'NIST' in compound and ('100' in compound or '1-100' in compound):
                nist_ref_row = idx
                print(f"Found NIST reference row at index {idx}: {row.iloc[0]}")
                break
        
        if nist_ref_row is not None:
            print(f"\n🧮 ORIGINAL CALCULATION ANALYSIS:")
            
            # Get first compound's data
            first_compound_ratio = original_ratio_sheet.iloc[0]
            nist_reference_data = original_ratio_sheet.iloc[nist_ref_row]
            first_compound_nist_result = original_nist_sheet.iloc[0]
            
            print(f"Compound: {first_compound_ratio.iloc[0]}")
            
            # Check calculation for first sample
            sample_col = sample_cols[0]
            ratio_value = first_compound_ratio[sample_col]
            
            # Map sample to NIST column (this is where the issue might be)
            # Original uses complex mapping - let's see what NIST value it uses
            
            # Try each NIST column to see which gives the right result
            expected_nist_result = first_compound_nist_result[sample_col]
            
            print(f"\nFor sample {sample_col}:")
            print(f"  Ratio: {ratio_value}")
            print(f"  Expected NIST result: {expected_nist_result}")
            
            for nist_col in nist_cols:
                nist_ref_value = nist_reference_data[nist_col]
                if pd.notna(nist_ref_value) and nist_ref_value != 0:
                    calculated_nist = ratio_value / nist_ref_value
                    print(f"  Using {nist_col} ({nist_ref_value}): {calculated_nist}")
                    if abs(calculated_nist - expected_nist_result) < 0.01:
                        print(f"    ✅ MATCH! This is the correct NIST reference")
                    else:
                        print(f"    ❌ No match (diff: {abs(calculated_nist - expected_nist_result)})")
        
        print(f"\n🔧 IDENTIFYING THE PROBLEM:")
        print("The issue is likely one of these:")
        print("1. Wrong NIST reference value being used")
        print("2. Wrong ratio calculation (should use pre-calculated ratios, not raw areas)")
        print("3. Wrong sample-to-NIST mapping logic")
        
        # Check if we should use ratio sheet directly vs calculating from areas
        print(f"\n📊 RATIO vs AREA ANALYSIS:")
        if 'Area Compound' in original_data:
            area_sheet = original_data['Area Compound']
            
            # Compare first compound's first sample
            area_value = area_sheet.iloc[0, 1]  # First compound, first sample
            ratio_value = original_ratio_sheet.iloc[0, 1]  # Same position
            
            print(f"Area value: {area_value}")
            print(f"Ratio value: {ratio_value}")
            
            if pd.notna(area_value) and pd.notna(ratio_value):
                if abs(area_value - ratio_value) < 0.01:
                    print("✅ Ratio sheet contains ratios, not raw areas")
                else:
                    print("❌ Ratio sheet might contain pre-calculated ratios")
                    print("This means we should NOT calculate ratios from areas!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_nist_issue()