#!/usr/bin/env python3

"""
FIXED RATIO PREVIEW TABLE
Correctly maps Sample Index (1-100) to actual sample names (PH-HC_5601-5700)
Uses the same counting logic: 25 samples per NIST column
"""

import pandas as pd
import numpy as np
import os

def create_fixed_ratio_preview():
    """
    Create ratio preview with correct Sample Index mapping
    """
    
    print("🎯 FIXED RATIO CALCULATION PREVIEW")
    print("=" * 80)
    
    excel_file = 'Calculate_alysis.xlsx'
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        return
    
    try:
        # Load all required sheets
        print("\n📊 LOADING EXCEL SHEETS...")
        area_data = pd.read_excel(excel_file, sheet_name='PH-HC_5601-5700')
        sample_index = pd.read_excel(excel_file, sheet_name='Sample index')
        compound_index = pd.read_excel(excel_file, sheet_name='Compound index')
        
        print(f"✅ Area Data: {area_data.shape}")
        print(f"✅ Sample Index: {sample_index.shape}")
        print(f"✅ Compound Index: {compound_index.shape}")
        
        # Get basic structure info
        compound_col = area_data.columns[0]
        compounds = area_data[compound_col].dropna().astype(str).str.strip()
        
        # Find sample and NIST columns
        sample_columns = [col for col in area_data.columns[1:] if 'PH-HC_' in str(col)]
        nist_columns = [col for col in area_data.columns[1:] if 'NIST' in str(col)]
        
        print(f"✅ Found {len(sample_columns)} sample columns, {len(nist_columns)} NIST columns")
        print(f"📊 Sample columns: {sample_columns[:5]}...")
        print(f"📊 NIST columns: {nist_columns}")
        
        # Build compound → ISTD mapping
        print("\n🔗 BUILDING COMPOUND → ISTD MAPPING...")
        compound_istd_map = {}
        comp_col = compound_index.columns[0]
        istd_col = compound_index.columns[1]
        
        for _, row in compound_index.iterrows():
            compound_name = str(row[comp_col]).strip()
            istd_name = str(row[istd_col]).strip()
            compound_istd_map[compound_name] = istd_name
        
        print(f"✅ Built mapping for {len(compound_istd_map)} compounds")
        
        # Create CORRECTED sample-to-NIST mapping using position logic
        print(f"\n🗺️ CREATING CORRECTED SAMPLE → NIST MAPPING...")
        print("Using position logic: samples 1-25 → NIST(1), 26-50 → NIST(2), etc.")
        
        # Extract Sample Index NIST pattern
        sample_index_nist = sample_index.iloc[:, 1].tolist()  # Get NIST column names from Sample Index
        
        print(f"📊 Sample Index NIST pattern: {set(sample_index_nist)}")
        
        # Build corrected mapping: actual samples → appropriate NIST
        corrected_sample_nist_map = {}
        
        for i, actual_sample in enumerate(sample_columns):
            # Position within 100 samples (0-based index → 1-based position)
            position = i + 1
            
            # Map to Sample Index position (1-100)
            sample_index_position = position - 1  # Convert to 0-based for Sample Index
            
            if sample_index_position < len(sample_index_nist):
                nist_from_index = sample_index_nist[sample_index_position]
                
                # Find matching NIST column in actual data
                matching_nist_col = None
                for nist_col in nist_columns:
                    # Match pattern: NIST_5601-5700 (1) ↔ NIST_1-100 (1)
                    if '(1)' in nist_from_index and '(1)' in str(nist_col):
                        matching_nist_col = nist_col
                        break
                    elif '(2)' in nist_from_index and '(2)' in str(nist_col):
                        matching_nist_col = nist_col
                        break
                    elif '(3)' in nist_from_index and '(3)' in str(nist_col):
                        matching_nist_col = nist_col
                        break
                    elif '(4)' in nist_from_index and '(4)' in str(nist_col):
                        matching_nist_col = nist_col
                        break
                
                corrected_sample_nist_map[actual_sample] = matching_nist_col
        
        print(f"✅ Built corrected mapping for {len(corrected_sample_nist_map)} samples")
        
        # Show mapping examples
        print(f"\n📋 CORRECTED MAPPING EXAMPLES:")
        for i, (sample, nist) in enumerate(list(corrected_sample_nist_map.items())[:10]):
            sample_index_ref = sample_index.iloc[i, 1] if i < len(sample_index) else 'N/A'
            print(f"  {sample} → {nist} (Index: {sample_index_ref})")
        
        # Create comprehensive preview for key compounds
        target_compounds = ['AcylCarnitine 10:0', 'AcylCarnitine 12:0', 'AcylCarnitine 12:1']
        target_samples = sample_columns[:5] if len(sample_columns) >= 5 else sample_columns
        
        print(f"\n📋 CREATING COMPREHENSIVE RATIO PREVIEW")
        print(f"Target Compounds: {target_compounds}")
        print(f"Target Samples: {target_samples}")
        print("=" * 100)
        
        # Create preview table
        preview_data = []
        
        for compound_name in target_compounds:
            # Find compound in data
            compound_idx = None
            for idx, comp in enumerate(compounds):
                if compound_name in str(comp):
                    compound_idx = idx
                    break
            
            if compound_idx is None:
                print(f"⚠️ {compound_name} not found in data")
                continue
            
            # Get ISTD for this compound
            istd_name = compound_istd_map.get(compound_name, None)
            if not istd_name:
                print(f"⚠️ No ISTD found for {compound_name}")
                continue
            
            # Find ISTD in data
            istd_idx = None
            for idx, comp in enumerate(compounds):
                if istd_name in str(comp):
                    istd_idx = idx
                    break
            
            if istd_idx is None:
                print(f"⚠️ ISTD {istd_name} not found in data for {compound_name}")
                continue
            
            print(f"\n🧮 {compound_name} (ISTD: {istd_name})")
            print("-" * 80)
            
            # Process each sample column
            for sample_col in target_samples:
                # Get areas
                compound_area = area_data.iloc[compound_idx][sample_col]
                istd_area = area_data.iloc[istd_idx][sample_col]
                
                # Calculate sample ratio
                sample_ratio = None
                if pd.notna(compound_area) and pd.notna(istd_area) and istd_area != 0:
                    sample_ratio = float(compound_area) / float(istd_area)
                
                # Get corresponding NIST column using corrected mapping
                nist_column = corrected_sample_nist_map.get(sample_col, None)
                
                # Get NIST areas and calculate NIST ratio
                nist_ratio = None
                nist_compound_area = None
                nist_istd_area = None
                
                if nist_column:
                    nist_compound_area = area_data.iloc[compound_idx][nist_column]
                    nist_istd_area = area_data.iloc[istd_idx][nist_column]
                    
                    if pd.notna(nist_compound_area) and pd.notna(nist_istd_area) and nist_istd_area != 0:
                        nist_ratio = float(nist_compound_area) / float(nist_istd_area)
                
                # Calculate NIST result
                nist_result = None
                if sample_ratio is not None and nist_ratio is not None and nist_ratio != 0:
                    nist_result = sample_ratio / nist_ratio
                
                # Add to preview data
                preview_row = {
                    'Compound': compound_name,
                    'ISTD': istd_name,
                    'Sample': sample_col,
                    'NIST_Column': nist_column or 'N/A',
                    'Sample_Compound_Area': f"{compound_area:,.0f}" if pd.notna(compound_area) else 'N/A',
                    'Sample_ISTD_Area': f"{istd_area:,.0f}" if pd.notna(istd_area) else 'N/A',
                    'Sample_Ratio': f"{sample_ratio:.6f}" if sample_ratio is not None else 'N/A',
                    'NIST_Compound_Area': f"{nist_compound_area:,.0f}" if pd.notna(nist_compound_area) else 'N/A',
                    'NIST_ISTD_Area': f"{nist_istd_area:,.0f}" if pd.notna(nist_istd_area) else 'N/A',
                    'NIST_Ratio': f"{nist_ratio:.6f}" if nist_ratio is not None else 'N/A',
                    'NIST_Result': f"{nist_result:.4f}" if nist_result is not None else 'N/A'
                }
                preview_data.append(preview_row)
                
                # Print detailed calculation
                print(f"Sample: {sample_col} → NIST: {nist_column or 'N/A'}")
                print(f"  Sample Areas: {compound_area:>10,.0f} ÷ {istd_area:>10,.0f} = {sample_ratio:.6f}" if sample_ratio else "  Sample Ratio: N/A")
                print(f"  NIST Areas:   {nist_compound_area:>10,.0f} ÷ {nist_istd_area:>10,.0f} = {nist_ratio:.6f}" if nist_ratio else "  NIST Ratio: N/A")
                print(f"  NIST Result:  {sample_ratio:.6f} ÷ {nist_ratio:.6f} = {nist_result:.4f}" if nist_result else "  NIST Result: N/A")
                print()
        
        # Create and display summary table
        if preview_data:
            print(f"\n📊 COMPREHENSIVE RATIO PREVIEW TABLE")
            print("=" * 150)
            
            preview_df = pd.DataFrame(preview_data)
            
            # Display formatted table
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', 20)
            
            print(preview_df.to_string(index=False))
            
            # Save to CSV for further analysis
            csv_filename = 'fixed_ratio_preview_table.csv'
            preview_df.to_csv(csv_filename, index=False)
            print(f"\n✅ Fixed preview table saved to: {csv_filename}")
        
        # Focus on AcylCarnitine 12:0 validation
        print(f"\n🎯 ACYLCARNITINE 12:0 VALIDATION")
        print("=" * 60)
        
        acyl_12_0_data = [row for row in preview_data if 'AcylCarnitine 12:0' in row['Compound']]
        
        if acyl_12_0_data:
            for row in acyl_12_0_data:
                print(f"Sample: {row['Sample']}")
                print(f"  NIST Column: {row['NIST_Column']}")
                print(f"  Sample Ratio: {row['Sample_Ratio']}")
                print(f"  NIST Ratio: {row['NIST_Ratio']}")
                print(f"  NIST Result: {row['NIST_Result']}")
                print()
        
        # Expected vs Calculated comparison for AcylCarnitine 12:0
        print(f"\n🔍 EXPECTED VS CALCULATED NIST RATIOS")
        print("=" * 60)
        
        expected_ratios = {
            'NIST_5601-5700 (1)': 0.0951,
            'NIST_5601-5700 (2)': 0.0985,
            'NIST_5601-5700 (3)': 0.0990,
            'NIST_5601-5700 (4)': 0.0949
        }
        
        for row in acyl_12_0_data:
            nist_col = row['NIST_Column']
            calculated_ratio = row['NIST_Ratio']
            
            for expected_col, expected_ratio in expected_ratios.items():
                if nist_col == expected_col:
                    if calculated_ratio != 'N/A':
                        calc_val = float(calculated_ratio)
                        match = abs(calc_val - expected_ratio) < 0.0001
                        status = "✅ PERFECT MATCH" if match else "❌ MISMATCH"
                        print(f"{status} {expected_col}")
                        print(f"  Expected: {expected_ratio:.6f}")
                        print(f"  Calculated: {calculated_ratio}")
                        print(f"  Difference: {abs(calc_val - expected_ratio):.6f}")
                    else:
                        print(f"❌ {expected_col}: Calculated ratio is N/A")
                    break
    
    except Exception as e:
        print(f"❌ Error creating fixed ratio preview: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_fixed_ratio_preview()