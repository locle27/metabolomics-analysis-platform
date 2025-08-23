#!/usr/bin/env python3

"""
COMPLETE RATIO SHEET CALCULATION ENGINE
Reads 3 input sheets and generates the complete Ratio sheet
Then uses Ratio sheet to calculate NIST results
"""

import pandas as pd
import numpy as np
import sys
import os

class RatioSheetCalculator:
    """
    Complete calculation engine that:
    1. Reads 3 input sheets (Area Compound, Sample Index, Compound Index)
    2. Calculates complete Ratio sheet 
    3. Uses Ratio sheet for NIST calculations
    """
    
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.area_data = None
        self.sample_index = None
        self.compound_index = None
        self.ratio_sheet = None
        
    def load_input_sheets(self):
        """Load the 3 required input sheets"""
        
        print("📊 LOADING INPUT SHEETS")
        print("=" * 50)
        
        try:
            # Load Area Compound sheet
            self.area_data = pd.read_excel(self.excel_file_path, sheet_name='PH-HC_5601-5700')
            print(f"✅ Area Compound loaded: {self.area_data.shape}")
            
            # Load Sample Index sheet  
            self.sample_index = pd.read_excel(self.excel_file_path, sheet_name='Sample index')
            print(f"✅ Sample Index loaded: {self.sample_index.shape}")
            
            # Load Compound Index sheet
            self.compound_index = pd.read_excel(self.excel_file_path, sheet_name='Compound index') 
            print(f"✅ Compound Index loaded: {self.compound_index.shape}")
            
            # Show column structures
            print(f"\n📋 Area Compound columns: {list(self.area_data.columns)[:5]}... ({len(self.area_data.columns)} total)")
            print(f"📋 Sample Index columns: {list(self.sample_index.columns)}")
            print(f"📋 Compound Index columns: {list(self.compound_index.columns)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading sheets: {e}")
            return False
    
    def analyze_data_structure(self):
        """Analyze the data structure to understand layout"""
        
        print(f"\n🔍 ANALYZING DATA STRUCTURE")
        print("=" * 50)
        
        # Analyze Area Compound sheet structure
        compound_column = self.area_data.columns[0]
        compounds = self.area_data[compound_column].dropna().astype(str).str.strip()
        
        print(f"📊 Compound column: '{compound_column}'")
        print(f"📊 Total compounds: {len(compounds)}")
        print(f"📊 First 5 compounds: {list(compounds.head())}")
        
        # Identify sample and NIST columns
        data_columns = self.area_data.columns[1:]  # Skip first compound column
        sample_columns = [col for col in data_columns if 'PH-HC_' in str(col)]
        nist_columns = [col for col in data_columns if 'NIST' in str(col)]
        
        print(f"📊 Sample columns: {len(sample_columns)} (e.g., {sample_columns[:3] if sample_columns else 'None'})")
        print(f"📊 NIST columns: {len(nist_columns)} (e.g., {nist_columns[:3] if nist_columns else 'None'})")
        
        # Analyze Sample Index structure
        if len(self.sample_index.columns) >= 2:
            sample_col = self.sample_index.columns[0]
            nist_col = self.sample_index.columns[1]
            print(f"📊 Sample Index mapping: {sample_col} → {nist_col}")
            print(f"📊 Sample mappings count: {len(self.sample_index)}")
            print(f"📊 First 5 mappings:")
            for i in range(min(5, len(self.sample_index))):
                sample = self.sample_index.iloc[i, 0]
                nist = self.sample_index.iloc[i, 1]
                print(f"    {sample} → {nist}")
        
        # Analyze Compound Index structure
        if len(self.compound_index.columns) >= 2:
            comp_col = self.compound_index.columns[0]
            istd_col = self.compound_index.columns[1]
            print(f"📊 Compound Index mapping: {comp_col} → {istd_col}")
            print(f"📊 Compound mappings count: {len(self.compound_index)}")
            print(f"📊 First 5 compound mappings:")
            for i in range(min(5, len(self.compound_index))):
                compound = self.compound_index.iloc[i, 0]
                istd = self.compound_index.iloc[i, 1]
                print(f"    {compound} → {istd}")
        
        return {
            'compounds': compounds,
            'sample_columns': sample_columns,
            'nist_columns': nist_columns,
            'compound_column': compound_column
        }
    
    def build_compound_istd_mapping(self, compounds):
        """Build mapping from compound name to ISTD name"""
        
        print(f"\n🔗 BUILDING COMPOUND → ISTD MAPPING")
        print("=" * 50)
        
        compound_istd_map = {}
        comp_col = self.compound_index.columns[0] 
        istd_col = self.compound_index.columns[1]
        
        # Create mapping from Compound Index sheet
        for _, row in self.compound_index.iterrows():
            compound_name = str(row[comp_col]).strip()
            istd_name = str(row[istd_col]).strip()
            compound_istd_map[compound_name] = istd_name
        
        print(f"✅ Built mapping for {len(compound_istd_map)} compounds")
        
        # Verify mapping for key compounds
        test_compounds = ['AcylCarnitine 10:0', 'AcylCarnitine 12:0', 'AcylCarnitine 12:1']
        for test_comp in test_compounds:
            if test_comp in compound_istd_map:
                print(f"✅ {test_comp} → {compound_istd_map[test_comp]}")
            else:
                print(f"❌ {test_comp} → NOT FOUND")
        
        return compound_istd_map
    
    def calculate_ratio_sheet(self, structure_info, compound_istd_map):
        """Calculate the complete Ratio sheet"""
        
        print(f"\n⚙️ CALCULATING COMPLETE RATIO SHEET")
        print("=" * 50)
        
        compounds = structure_info['compounds']
        all_data_columns = structure_info['sample_columns'] + structure_info['nist_columns']
        compound_column = structure_info['compound_column']
        
        print(f"📊 Processing {len(compounds)} compounds across {len(all_data_columns)} columns")
        
        # Initialize ratio sheet with same structure as area data
        self.ratio_sheet = self.area_data.copy()
        
        # Calculate ratios for each compound in each column
        calculated_count = 0
        error_count = 0
        
        for compound_idx, compound_name in enumerate(compounds):
            compound_name = str(compound_name).strip()
            
            # Find ISTD for this compound
            istd_name = compound_istd_map.get(compound_name, None)
            
            if not istd_name:
                print(f"⚠️ No ISTD found for {compound_name}, skipping...")
                continue
            
            # Find ISTD row index
            istd_row_idx = None
            for idx, comp in enumerate(compounds):
                if str(comp).strip() == istd_name:
                    istd_row_idx = idx
                    break
            
            if istd_row_idx is None:
                print(f"⚠️ ISTD '{istd_name}' not found in compound list for {compound_name}")
                continue
            
            # Calculate ratios for this compound across all columns
            for column in all_data_columns:
                try:
                    compound_area = self.area_data.iloc[compound_idx][column]
                    istd_area = self.area_data.iloc[istd_row_idx][column]
                    
                    if pd.notna(compound_area) and pd.notna(istd_area) and istd_area != 0:
                        ratio = float(compound_area) / float(istd_area)
                        self.ratio_sheet.iloc[compound_idx, self.ratio_sheet.columns.get_loc(column)] = ratio
                        calculated_count += 1
                    else:
                        self.ratio_sheet.iloc[compound_idx, self.ratio_sheet.columns.get_loc(column)] = np.nan
                        error_count += 1
                
                except Exception as e:
                    print(f"❌ Error calculating ratio for {compound_name} in {column}: {e}")
                    self.ratio_sheet.iloc[compound_idx, self.ratio_sheet.columns.get_loc(column)] = np.nan
                    error_count += 1
            
            # Progress reporting
            if (compound_idx + 1) % 50 == 0:
                print(f"📊 Processed {compound_idx + 1}/{len(compounds)} compounds...")
        
        print(f"✅ Ratio calculation complete!")
        print(f"✅ Successful calculations: {calculated_count}")
        print(f"⚠️ Failed calculations: {error_count}")
        
        return True
    
    def verify_ratio_calculations(self, structure_info):
        """Verify ratio calculations with known examples"""
        
        print(f"\n🔍 VERIFYING RATIO CALCULATIONS")
        print("=" * 50)
        
        # Test AcylCarnitine 12:0 in NIST columns
        test_compound = 'AcylCarnitine 12:0'
        nist_columns = structure_info['nist_columns']
        
        # Find AcylCarnitine 12:0 row
        compounds = structure_info['compounds']
        test_row_idx = None
        for idx, compound in enumerate(compounds):
            if 'AcylCarnitine 12:0' in str(compound):
                test_row_idx = idx
                break
        
        if test_row_idx is None:
            print(f"❌ {test_compound} not found for verification")
            return
        
        print(f"✅ Found {test_compound} at row {test_row_idx}")
        
        # Check calculated ratios vs expected values
        expected_ratios = {
            'NIST_5601-5700 (1)': 0.0951,
            'NIST_5601-5700 (2)': 0.0985,
            'NIST_5601-5700 (3)': 0.0990,
            'NIST_5601-5700 (4)': 0.0949
        }
        
        print(f"\n📊 {test_compound} RATIO VERIFICATION:")
        for expected_col, expected_ratio in expected_ratios.items():
            # Find matching column (handle spacing variations)
            matching_col = None
            for nist_col in nist_columns:
                if expected_col.replace(' ', '') == str(nist_col).replace(' ', ''):
                    matching_col = nist_col
                    break
            
            if matching_col:
                calculated_ratio = self.ratio_sheet.iloc[test_row_idx][matching_col]
                if pd.notna(calculated_ratio):
                    match_status = "✅" if abs(calculated_ratio - expected_ratio) < 0.0001 else "❌"
                    print(f"  {match_status} {expected_col}: Expected {expected_ratio:.6f}, Calculated {calculated_ratio:.6f}")
                else:
                    print(f"  ❌ {expected_col}: Calculated ratio is NaN")
            else:
                print(f"  ❌ {expected_col}: Column not found in data")
    
    def calculate_nist_results(self, structure_info):
        """Use Ratio sheet to calculate NIST results for samples"""
        
        print(f"\n🎯 CALCULATING NIST RESULTS USING RATIO SHEET")
        print("=" * 50)
        
        sample_columns = structure_info['sample_columns']
        compounds = structure_info['compounds']
        
        # Build sample to NIST mapping
        sample_nist_map = {}
        for _, row in self.sample_index.iterrows():
            sample = str(row.iloc[0]).strip()
            nist = str(row.iloc[1]).strip()
            sample_nist_map[sample] = nist
        
        print(f"📊 Sample mappings: {len(sample_nist_map)}")
        
        # Test calculation for AcylCarnitine 12:0 in first sample
        test_compound = 'AcylCarnitine 12:0'
        test_sample = sample_columns[0] if sample_columns else None
        
        if test_sample and test_compound:
            # Find compound row
            test_row_idx = None
            for idx, compound in enumerate(compounds):
                if 'AcylCarnitine 12:0' in str(compound):
                    test_row_idx = idx
                    break
            
            if test_row_idx is not None:
                # Get sample ratio from Ratio sheet
                sample_ratio = self.ratio_sheet.iloc[test_row_idx][test_sample]
                
                # Find corresponding NIST column
                nist_column = sample_nist_map.get(test_sample)
                
                if nist_column and pd.notna(sample_ratio):
                    # Find matching NIST column in ratio sheet
                    matching_nist_col = None
                    for col in self.ratio_sheet.columns:
                        if str(col).replace(' ', '') == nist_column.replace(' ', ''):
                            matching_nist_col = col
                            break
                    
                    if matching_nist_col:
                        nist_ratio = self.ratio_sheet.iloc[test_row_idx][matching_nist_col]
                        
                        if pd.notna(nist_ratio) and nist_ratio != 0:
                            nist_result = sample_ratio / nist_ratio
                            
                            print(f"🧮 EXAMPLE CALCULATION:")
                            print(f"  Compound: {test_compound}")
                            print(f"  Sample: {test_sample}")
                            print(f"  Sample Ratio: {sample_ratio:.6f}")
                            print(f"  NIST Column: {nist_column}")
                            print(f"  NIST Ratio: {nist_ratio:.6f}")
                            print(f"  NIST Result: {sample_ratio:.6f} ÷ {nist_ratio:.6f} = {nist_result:.6f}")
                        else:
                            print(f"❌ Invalid NIST ratio: {nist_ratio}")
                    else:
                        print(f"❌ NIST column '{nist_column}' not found in ratio sheet")
                else:
                    print(f"❌ Sample calculation failed - sample_ratio: {sample_ratio}, nist_column: {nist_column}")
    
    def run_complete_calculation(self):
        """Run the complete calculation pipeline"""
        
        print("🚀 COMPLETE RATIO SHEET CALCULATION PIPELINE")
        print("=" * 70)
        
        # Step 1: Load input sheets
        if not self.load_input_sheets():
            return False
        
        # Step 2: Analyze data structure
        structure_info = self.analyze_data_structure()
        
        # Step 3: Build compound-ISTD mapping
        compound_istd_map = self.build_compound_istd_mapping(structure_info['compounds'])
        
        # Step 4: Calculate complete ratio sheet
        if not self.calculate_ratio_sheet(structure_info, compound_istd_map):
            return False
        
        # Step 5: Verify calculations
        self.verify_ratio_calculations(structure_info)
        
        # Step 6: Calculate NIST results using ratio sheet
        self.calculate_nist_results(structure_info)
        
        print(f"\n🎉 CALCULATION PIPELINE COMPLETE!")
        print(f"✅ Ratio sheet generated with {self.ratio_sheet.shape} dimensions")
        print(f"✅ Ready for NIST result calculations")
        
        return True

def main():
    """Main execution function"""
    
    excel_file = 'Calculate_alysis.xlsx'
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        sys.exit(1)
    
    calculator = RatioSheetCalculator(excel_file)
    
    if calculator.run_complete_calculation():
        print(f"\n✅ SUCCESS: Complete ratio calculation system working!")
    else:
        print(f"\n❌ FAILED: Ratio calculation system encountered errors")

if __name__ == "__main__":
    main()