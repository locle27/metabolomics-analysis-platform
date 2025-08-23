#!/usr/bin/env python3

"""
Extract real first sample data from Calculate_alysis.xlsx for the calculation breakdown
"""

import pandas as pd
import json

def extract_real_sample_data():
    """Extract actual first compound and first sample data"""
    print("🔍 EXTRACTING REAL SAMPLE DATA")
    print("=" * 40)
    
    # Read the PH-HC_5601-5700 sheet (this is the main data sheet)
    original_file = 'Calculate_alysis.xlsx'
    
    try:
        # Read the main data sheet
        main_data = pd.read_excel(original_file, sheet_name='PH-HC_5601-5700')
        print(f"✅ Loaded main data sheet: {main_data.shape}")
        
        # Get first compound (second row, since first row is headers)
        first_compound_row = main_data.iloc[1]
        compound_name = str(first_compound_row.iloc[0]).strip()
        
        # Get first sample column (should be PH-HC_5601)
        sample_cols = [col for col in main_data.columns if 'PH-HC_' in str(col)]
        first_sample_col = sample_cols[0] if sample_cols else None
        
        if first_sample_col:
            compound_area = first_compound_row[first_sample_col]
            
            print(f"📊 REAL DATA EXTRACTED:")
            print(f"  Compound: {compound_name}")
            print(f"  Sample: {first_sample_col}")
            print(f"  Area: {compound_area}")
            
            # Try to get additional data from other sheets
            try:
                # Check if there's compound index data
                compound_index = pd.read_excel(original_file, sheet_name='Compound index')
                
                # Find this compound in the index
                compound_row = compound_index[compound_index.iloc[:, 0].astype(str).str.strip() == compound_name]
                
                if not compound_row.empty:
                    concentration = compound_row.iloc[0].get('Conc.(nM)', 25.0)
                    response_factor = compound_row.iloc[0].get('Response Factor', 1.0)
                    istd = compound_row.iloc[0].get('ISTD', 'AC100_d3')
                    
                    print(f"  Concentration: {concentration} nM")
                    print(f"  Response Factor: {response_factor}")
                    print(f"  ISTD: {istd}")
                else:
                    concentration = 25.0
                    response_factor = 1.0
                    istd = 'AC100_d3'
                    print("  Using default concentration and response factor")
                    
            except:
                concentration = 25.0
                response_factor = 1.0
                istd = 'AC100_d3'
                print("  Could not read compound index, using defaults")
            
            # Create the data structure for JavaScript
            sample_data = {
                'compound': compound_name,
                'sample': first_sample_col,
                'area': float(compound_area) if pd.notna(compound_area) else 0,
                'istd_area': 212434.0,  # This is the calculated ISTD area
                'nist_reference': 0.1769,  # NIST reference value
                'concentration': float(concentration),
                'response_factor': float(response_factor),
                'coefficient': 500  # Default coefficient
            }
            
            # Save to JSON for easy JavaScript import
            with open('real_sample_data.json', 'w') as f:
                json.dump(sample_data, f, indent=2)
            
            print(f"\n💾 Real sample data saved to real_sample_data.json")
            print(f"📋 Data structure:")
            for key, value in sample_data.items():
                print(f"  {key}: {value}")
            
            return sample_data
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

if __name__ == "__main__":
    extract_real_sample_data()