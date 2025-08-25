#!/usr/bin/env python3
"""
Check if input Excel files contain NIST columns
"""

import pandas as pd
import os

def check_input_files_for_nist():
    """Check various Excel files for NIST columns"""
    
    files_to_check = [
        "PH-HC_5701-5800.xlsx",
        "area-compound.xlsx",
        "Calculate_alysis.xlsx"
    ]
    
    for excel_file in files_to_check:
        if os.path.exists(excel_file):
            print(f"\n{'=' * 80}")
            print(f"📊 ANALYZING FILE: {excel_file}")
            print('=' * 80)
            
            try:
                # For Calculate_alysis.xlsx, check specific sheets
                if excel_file == "Calculate_alysis.xlsx":
                    # First, get all sheet names
                    xl_file = pd.ExcelFile(excel_file)
                    print(f"📑 Available sheets: {xl_file.sheet_names}")
                    
                    # Check the PH-HC sheet
                    if 'PH-HC_5601-5700' in xl_file.sheet_names:
                        df = pd.read_excel(excel_file, sheet_name='PH-HC_5601-5700')
                        print(f"\n🔍 Sheet: PH-HC_5601-5700")
                        print(f"   Shape: {df.shape}")
                        print(f"   Columns ({len(df.columns)}):")
                        
                        # Group columns by type
                        nist_cols = []
                        ph_hc_cols = []
                        other_cols = []
                        
                        for col in df.columns:
                            if 'NIST' in str(col):
                                nist_cols.append(col)
                            elif 'PH-HC' in str(col):
                                ph_hc_cols.append(col)
                            else:
                                other_cols.append(col)
                        
                        print(f"\n   📌 NIST columns ({len(nist_cols)}):")
                        for col in nist_cols[:10]:  # First 10
                            print(f"      - '{col}'")
                        if len(nist_cols) > 10:
                            print(f"      ... and {len(nist_cols) - 10} more")
                        
                        print(f"\n   📌 PH-HC columns ({len(ph_hc_cols)}):")
                        for col in ph_hc_cols[:10]:  # First 10
                            print(f"      - '{col}'")
                        if len(ph_hc_cols) > 10:
                            print(f"      ... and {len(ph_hc_cols) - 10} more")
                        
                        print(f"\n   📌 Other columns ({len(other_cols)}):")
                        for col in other_cols[:5]:
                            print(f"      - '{col}'")
                        
                        # Analyze NIST column patterns
                        if nist_cols:
                            print(f"\n   🔍 NIST Column Pattern Analysis:")
                            patterns = {}
                            for col in nist_cols:
                                # Extract pattern
                                col_str = str(col)
                                if '_' in col_str and '(' in col_str:
                                    base = col_str.split('(')[0].strip()
                                    if base not in patterns:
                                        patterns[base] = []
                                    patterns[base].append(col_str)
                            
                            for pattern, cols in patterns.items():
                                print(f"      Pattern: '{pattern}' - {len(cols)} columns")
                
                else:
                    # For other files, just read the main sheet
                    df = pd.read_excel(excel_file)
                    print(f"📐 Shape: {df.shape}")
                    print(f"📋 Columns ({len(df.columns)}):")
                    
                    # Check for NIST columns
                    nist_cols = [col for col in df.columns if 'NIST' in str(col)]
                    ph_hc_cols = [col for col in df.columns if 'PH-HC' in str(col)]
                    
                    if nist_cols:
                        print(f"\n✅ Found {len(nist_cols)} NIST columns:")
                        for col in nist_cols[:10]:
                            print(f"   - '{col}'")
                    else:
                        print("\n❌ No NIST columns found")
                    
                    if ph_hc_cols:
                        print(f"\n✅ Found {len(ph_hc_cols)} PH-HC columns:")
                        for col in ph_hc_cols[:10]:
                            print(f"   - '{col}'")
                    
                    # Show all columns if small enough
                    if len(df.columns) <= 20:
                        print(f"\n📋 All columns:")
                        for i, col in enumerate(df.columns):
                            print(f"   {i+1}. '{col}'")
                
            except Exception as e:
                print(f"❌ Error reading {excel_file}: {e}")

if __name__ == "__main__":
    check_input_files_for_nist()