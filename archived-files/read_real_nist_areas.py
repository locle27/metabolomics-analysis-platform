#!/usr/bin/env python3

"""
Read the actual AcylCarnitine 12:0 area values from Calculate_alysis.xlsx
To understand the real NIST ratio calculation
"""

import pandas as pd
import numpy as np

def read_real_area_values():
    """Read actual area values from the Excel file"""
    
    try:
        print("📊 READING REAL AREA VALUES FROM EXCEL")
        print("=" * 60)
        
        # Read the main data sheet
        excel_file = 'Calculate_alysis.xlsx'
        main_data = pd.read_excel(excel_file, sheet_name='PH-HC_5601-5700')
        
        print(f"✅ Loaded Excel sheet: {main_data.shape}")
        print(f"📋 Columns: {list(main_data.columns)}")
        
        # Find AcylCarnitine 12:0 row
        compound_col = main_data.columns[0]  # First column should be compounds
        acylcarnitine_12_0_idx = None
        
        for idx, compound in enumerate(main_data[compound_col]):
            if 'AcylCarnitine 12:0' in str(compound):
                acylcarnitine_12_0_idx = idx
                print(f"🎯 Found AcylCarnitine 12:0 at row {idx}: '{compound}'")
                break
        
        if acylcarnitine_12_0_idx is None:
            print("❌ AcylCarnitine 12:0 not found!")
            return
        
        # Find NIST columns
        nist_columns = [col for col in main_data.columns if 'NIST' in str(col)]
        print(f"📊 Found {len(nist_columns)} NIST columns:")
        for col in nist_columns:
            print(f"  - {col}")
        
        # Get AcylCarnitine 12:0 values in all NIST columns
        print(f"\n🧮 AcylCarnitine 12:0 AREA VALUES:")
        acyl_12_0_row = main_data.iloc[acylcarnitine_12_0_idx]
        
        for nist_col in nist_columns:
            area_value = acyl_12_0_row[nist_col]
            print(f"  {nist_col}: {area_value}")
        
        # Read Compound Index to find ISTD for AcylCarnitine 12:0
        print(f"\n🔍 FINDING ISTD FOR AcylCarnitine 12:0:")
        try:
            compound_index = pd.read_excel(excel_file, sheet_name='Compound index')
            
            # Find AcylCarnitine 12:0 in compound index
            acyl_compound_row = None
            for idx, row in compound_index.iterrows():
                if 'AcylCarnitine 12:0' in str(row.iloc[0]):
                    acyl_compound_row = row
                    istd_name = row.iloc[1] if len(row) > 1 else 'Unknown'
                    print(f"  AcylCarnitine 12:0 ISTD: {istd_name}")
                    break
            
            if acyl_compound_row is None:
                print("  ❌ AcylCarnitine 12:0 not found in Compound Index")
                istd_name = 'LPC 18:1 d7'  # Fallback based on your data
                print(f"  Using fallback ISTD: {istd_name}")
        except:
            print("  ⚠️ Could not read Compound Index sheet")
            istd_name = 'LPC 18:1 d7'  # Fallback
            print(f"  Using fallback ISTD: {istd_name}")
        
        # Find ISTD row and get its area values
        print(f"\n🔍 FINDING ISTD AREA VALUES:")
        istd_idx = None
        for idx, compound in enumerate(main_data[compound_col]):
            if istd_name in str(compound):
                istd_idx = idx
                print(f"  Found {istd_name} at row {idx}")
                break
        
        if istd_idx is not None:
            istd_row = main_data.iloc[istd_idx]
            
            print(f"\n📊 {istd_name} AREA VALUES:")
            for nist_col in nist_columns:
                istd_area = istd_row[nist_col]
                print(f"  {nist_col}: {istd_area}")
            
            # Calculate actual NIST ratios
            print(f"\n🧮 CALCULATED NIST RATIOS (AcylCarnitine 12:0 ÷ {istd_name}):")
            for nist_col in nist_columns:
                compound_area = acyl_12_0_row[nist_col]
                istd_area = istd_row[nist_col]
                
                if pd.notna(compound_area) and pd.notna(istd_area) and istd_area != 0:
                    ratio = float(compound_area) / float(istd_area)
                    print(f"  {nist_col}: {compound_area:,.0f} ÷ {istd_area:,.0f} = {ratio:.6f}")
                else:
                    print(f"  {nist_col}: Invalid data (compound: {compound_area}, istd: {istd_area})")
        else:
            print(f"  ❌ {istd_name} not found in data")
        
        # Compare with expected ratios from your data
        print(f"\n🎯 COMPARISON WITH EXPECTED RATIOS:")
        expected_ratios = {
            'NIST_5601-5700 (1)': 0.0951,
            'NIST_5601-5700 (2)': 0.0985,
            'NIST_5601-5700 (3)': 0.0990,
            'NIST_5601-5700 (4)': 0.0949
        }
        
        for expected_col, expected_ratio in expected_ratios.items():
            # Find matching column (handle spacing variations)
            matching_col = None
            for nist_col in nist_columns:
                if expected_col.replace(' ', '') == str(nist_col).replace(' ', ''):
                    matching_col = nist_col
                    break
            
            if matching_col:
                compound_area = acyl_12_0_row[matching_col]
                if istd_idx is not None:
                    istd_area = main_data.iloc[istd_idx][matching_col]
                    if pd.notna(compound_area) and pd.notna(istd_area) and istd_area != 0:
                        calculated_ratio = float(compound_area) / float(istd_area)
                        match_status = "✅" if abs(calculated_ratio - expected_ratio) < 0.0001 else "❌"
                        print(f"  {match_status} {expected_col}: Expected {expected_ratio:.6f}, Calculated {calculated_ratio:.6f}")
                    else:
                        print(f"  ❌ {expected_col}: Invalid data")
            else:
                print(f"  ❌ {expected_col}: Column not found")
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    read_real_area_values()