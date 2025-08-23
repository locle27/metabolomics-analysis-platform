#!/usr/bin/env python3

"""
Extract correct NIST ratios from Excel file to fix web app calculations
"""

import pandas as pd
import sys
import os

def extract_nist_ratios():
    """Extract NIST ratios by comparing sample ratios with Excel NIST results"""
    
    try:
        # Read the Excel file
        excel_file = 'Calculate_alysis.xlsx'
        print(f"📊 Reading {excel_file}...")
        
        excel_data = pd.read_excel(excel_file, sheet_name=None)
        print(f"✅ Found {len(excel_data)} sheets: {list(excel_data.keys())}")
        
        # Get the main data sheet (area data)
        area_sheet_name = None
        ratio_sheet_name = None
        nist_sheet_name = None
        
        for sheet_name in excel_data.keys():
            if 'PH-HC_' in sheet_name and ('5601' in sheet_name or '5701' in sheet_name):
                area_sheet_name = sheet_name
            elif 'Ratio' in sheet_name:
                ratio_sheet_name = sheet_name
            elif 'NIST' in sheet_name:
                nist_sheet_name = sheet_name
        
        print(f"📋 Area sheet: {area_sheet_name}")
        print(f"📋 Ratio sheet: {ratio_sheet_name}")  
        print(f"📋 NIST sheet: {nist_sheet_name}")
        
        if not all([ratio_sheet_name, nist_sheet_name]):
            print("❌ Missing required sheets!")
            return
            
        # Read the sheets
        ratio_data = excel_data[ratio_sheet_name]
        nist_data = excel_data[nist_sheet_name]
        
        print(f"\n📊 Ratio data shape: {ratio_data.shape}")
        print(f"📊 NIST data shape: {nist_data.shape}")
        
        # Get compound names (first column)
        compounds = ratio_data.iloc[:, 0].tolist()
        nist_compounds = nist_data.iloc[:, 0].tolist()
        
        print(f"\n🧪 Found {len(compounds)} compounds in ratio sheet")
        print(f"🧪 Found {len(nist_compounds)} compounds in NIST sheet")
        
        # Get sample columns
        ratio_sample_cols = [col for col in ratio_data.columns if 'PH-HC_' in str(col)]
        nist_sample_cols = [col for col in nist_data.columns if 'PH-HC_' in str(col)]
        
        print(f"\n📋 Ratio sample columns: {ratio_sample_cols[:5]}...")
        print(f"📋 NIST sample columns: {nist_sample_cols[:5]}...")
        
        # Calculate NIST ratios for each compound
        compound_nist_ratios = {}
        
        for i, compound in enumerate(compounds[:20]):  # Process first 20 compounds
            if pd.isna(compound) or compound == '':
                continue
                
            compound_clean = str(compound).strip()
            
            # Find matching compound in NIST sheet
            nist_row_idx = None
            for j, nist_compound in enumerate(nist_compounds):
                if str(nist_compound).strip() == compound_clean:
                    nist_row_idx = j
                    break
            
            if nist_row_idx is None:
                print(f"⚠️ Compound '{compound_clean}' not found in NIST sheet")
                continue
            
            # Get sample ratios and NIST results for first few samples
            sample_ratios = []
            nist_results = []
            calculated_nist_ratios = []
            
            for sample_col in ratio_sample_cols[:3]:  # First 3 samples
                if sample_col in nist_sample_cols:
                    try:
                        sample_ratio = ratio_data.iloc[i][sample_col]
                        nist_result = nist_data.iloc[nist_row_idx][sample_col]
                        
                        if pd.notna(sample_ratio) and pd.notna(nist_result) and float(nist_result) != 0:
                            calculated_nist_ratio = float(sample_ratio) / float(nist_result)
                            sample_ratios.append(float(sample_ratio))
                            nist_results.append(float(nist_result))
                            calculated_nist_ratios.append(calculated_nist_ratio)
                    except:
                        pass
            
            if calculated_nist_ratios:
                # Use average of calculated ratios (should be consistent)
                avg_nist_ratio = sum(calculated_nist_ratios) / len(calculated_nist_ratios)
                compound_nist_ratios[compound_clean] = round(avg_nist_ratio, 6)
                
                print(f"\n🔍 {compound_clean}:")
                print(f"  Sample ratios: {[round(r, 6) for r in sample_ratios]}")
                print(f"  NIST results:  {[round(r, 3) for r in nist_results]}")
                print(f"  Calculated NIST ratios: {[round(r, 6) for r in calculated_nist_ratios]}")
                print(f"  ✅ Average NIST ratio: {avg_nist_ratio:.6f}")
        
        # Generate Python code for the lookup table
        print(f"\n🔧 PYTHON CODE FOR NIST RATIO LOOKUP:")
        print("compound_nist_ratios = {")
        for compound, ratio in compound_nist_ratios.items():
            print(f"    '{compound}': {ratio},")
        print("}")
        
        print(f"\n✅ Extracted NIST ratios for {len(compound_nist_ratios)} compounds")
        
        return compound_nist_ratios
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_nist_ratios()