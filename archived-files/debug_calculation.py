#!/usr/bin/env python3

"""
Debug the calculation differences between the new system and original results
"""

import pandas as pd
import sys
import os

def debug_calculations():
    """Compare the uploaded file with original calculation results"""
    print("🔍 DEBUGGING NIST CALCULATION DIFFERENCES")
    print("=" * 60)
    
    # Read the uploaded file
    uploaded_file = 'Book1.xlsx'
    original_file = 'Calculate_alysis.xlsx'
    
    if not os.path.exists(uploaded_file):
        print(f"❌ Uploaded file not found: {uploaded_file}")
        return
    
    if not os.path.exists(original_file):
        print(f"❌ Original file not found: {original_file}")
        return
    
    try:
        # Read uploaded file
        print("📊 Reading uploaded file (Book1.xlsx)...")
        uploaded_data = pd.read_excel(uploaded_file, sheet_name=None)
        print(f"Sheets in uploaded file: {list(uploaded_data.keys())}")
        
        # Read original file for comparison
        print("📊 Reading original file (Calculate alysis.xlsx)...")
        original_data = pd.read_excel(original_file, sheet_name=None)
        print(f"Sheets in original file: {list(original_data.keys())}")
        
        # Get the main data from uploaded file
        main_sheet_name = list(uploaded_data.keys())[0]
        uploaded_main = uploaded_data[main_sheet_name]
        print(f"\n📋 Uploaded file main sheet: {main_sheet_name}")
        print(f"Shape: {uploaded_main.shape}")
        print(f"Columns: {list(uploaded_main.columns)[:10]}...")
        
        # Compare with original PH-HC_5601-5700 sheet
        if 'PH-HC_5601-5700' in original_data:
            original_main = original_data['PH-HC_5601-5700']
            print(f"\n📋 Original PH-HC_5601-5700 sheet:")
            print(f"Shape: {original_main.shape}")
            print(f"Columns: {list(original_main.columns)[:10]}...")
            
            # Compare first few compounds
            print(f"\n🔍 COMPARING FIRST 5 COMPOUNDS:")
            
            # Handle different header formats
            if uploaded_main.iloc[0, 0] == 'Name' or str(uploaded_main.iloc[0, 0]).lower() == 'name':
                uploaded_compounds = uploaded_main.iloc[1:6, 0]  # Skip header
                uploaded_areas = uploaded_main.iloc[1:6, 1:6]   # First 5 data columns
            else:
                uploaded_compounds = uploaded_main.iloc[0:5, 0]  # No header
                uploaded_areas = uploaded_main.iloc[0:5, 1:6]   # First 5 data columns
            
            if original_main.iloc[0, 0] == 'Name' or str(original_main.iloc[0, 0]).lower() == 'name':
                original_compounds = original_main.iloc[1:6, 0]  # Skip header
                original_areas = original_main.iloc[1:6, 1:6]   # First 5 data columns
            else:
                original_compounds = original_main.iloc[0:5, 0]  # No header
                original_areas = original_main.iloc[0:5, 1:6]   # First 5 data columns
            
            for i in range(min(5, len(uploaded_compounds), len(original_compounds))):
                up_compound = str(uploaded_compounds.iloc[i]).strip()
                orig_compound = str(original_compounds.iloc[i]).strip()
                print(f"  Row {i+1}: Uploaded='{up_compound}' | Original='{orig_compound}'")
                
                if up_compound == orig_compound:
                    print(f"    ✅ Compound names match")
                    # Compare first area value
                    up_area = uploaded_areas.iloc[i, 0] if i < len(uploaded_areas) else "N/A"
                    orig_area = original_areas.iloc[i, 0] if i < len(original_areas) else "N/A"
                    print(f"    Area values: Uploaded={up_area} | Original={orig_area}")
                else:
                    print(f"    ❌ Compound names don't match")
        
        # Now compare with original calculation results
        print(f"\n🎯 COMPARING WITH ORIGINAL NIST RESULTS:")
        if 'NIST' in original_data:
            original_nist = original_data['NIST']
            print(f"Original NIST sheet shape: {original_nist.shape}")
            print(f"Sample NIST results for first compound:")
            
            first_compound = original_nist.iloc[0, 0]
            first_values = original_nist.iloc[0, 1:6]  # First 5 values
            print(f"  Compound: {first_compound}")
            print(f"  Values: {list(first_values)}")
        
        # Check ratio calculation methodology
        print(f"\n🧮 CHECKING ORIGINAL RATIO METHODOLOGY:")
        if 'Ratio' in original_data:
            original_ratio = original_data['Ratio']
            print(f"Original Ratio sheet shape: {original_ratio.shape}")
            
            # Compare ratio vs area for first compound
            first_compound = original_ratio.iloc[0, 0]
            first_ratio_values = original_ratio.iloc[0, 1:4]  # First 3 values
            print(f"  Compound: {first_compound}")
            print(f"  Ratio values: {list(first_ratio_values)}")
            
            # Check if these are pre-calculated ratios or raw areas
            if 'Area Compound' in original_data:
                original_area = original_data['Area Compound']
                first_area_values = original_area.iloc[0, 1:4]  # First 3 values
                print(f"  Area values: {list(first_area_values)}")
                
                # Calculate expected ratio
                if len(first_area_values) > 0 and len(first_ratio_values) > 0:
                    area_val = first_area_values.iloc[0]
                    ratio_val = first_ratio_values.iloc[0]
                    if pd.notna(area_val) and pd.notna(ratio_val) and area_val != 0:
                        implied_istd = float(area_val) / float(ratio_val)
                        print(f"  Implied ISTD area: {implied_istd}")
        
        # Check NIST reference values used
        print(f"\n🎯 CHECKING NIST REFERENCE VALUES:")
        if 'Ratio' in original_data:
            ratio_sheet = original_data['Ratio']
            # Look for NIST columns
            nist_columns = [col for col in ratio_sheet.columns if 'NIST' in str(col).upper()]
            print(f"  NIST columns found: {nist_columns}")
            
            if nist_columns:
                # Get NIST reference row values
                for idx, row in ratio_sheet.iterrows():
                    compound = str(row.iloc[0]).strip().upper()
                    if 'NIST' in compound and ('100' in compound or '1-100' in compound):
                        print(f"  NIST reference row: {row.iloc[0]}")
                        for nist_col in nist_columns:
                            nist_val = row[nist_col]
                            print(f"    {nist_col}: {nist_val}")
                        break
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_calculations()