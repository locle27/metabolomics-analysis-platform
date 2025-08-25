#!/usr/bin/env python3
"""
Analyze NIST columns in Ratio-database.xlsx
"""

import pandas as pd
import os

def analyze_nist_columns():
    """Analyze the structure of NIST columns in Ratio-database.xlsx"""
    
    try:
        # Try to read the Ratio-database.xlsx file
        ratio_file = "Ratio-database.xlsx"
        
        if os.path.exists(ratio_file):
            print(f"📊 ANALYZING RATIO DATABASE: {ratio_file}")
            print("=" * 80)
            
            # Read the Excel file
            df = pd.read_excel(ratio_file)
            
            print(f"✅ Successfully loaded Ratio database")
            print(f"📐 Shape: {df.shape}")
            print(f"📋 All columns ({len(df.columns)}):")
            for i, col in enumerate(df.columns):
                print(f"   {i+1}. '{col}'")
            
            # Find NIST columns
            print("\n🔍 NIST-related columns:")
            nist_columns = []
            for col in df.columns:
                if 'NIST' in str(col):
                    nist_columns.append(col)
                    print(f"   - '{col}'")
            
            if not nist_columns:
                print("   ❌ No columns containing 'NIST' found")
                
                # Look for columns with parentheses which might be NIST patterns
                print("\n🔍 Columns with parentheses (potential NIST patterns):")
                paren_columns = []
                for col in df.columns:
                    if '(' in str(col) and ')' in str(col):
                        paren_columns.append(col)
                        print(f"   - '{col}'")
                
                if paren_columns:
                    nist_columns = paren_columns
            
            # Analyze first few rows
            print(f"\n📊 First 5 rows of data:")
            print(df.head().to_string())
            
            # Check if there's a Compound column
            compound_col = None
            for col in df.columns:
                if 'Compound' in str(col) or 'compound' in str(col):
                    compound_col = col
                    break
            
            if compound_col:
                print(f"\n✅ Found compound column: '{compound_col}'")
                print(f"   Sample compounds: {df[compound_col].head(10).tolist()}")
            
            # Analyze data types in NIST columns
            if nist_columns:
                print(f"\n📊 NIST column data analysis:")
                for nist_col in nist_columns[:5]:  # First 5 NIST columns
                    print(f"\n   Column: '{nist_col}'")
                    print(f"   - Data type: {df[nist_col].dtype}")
                    print(f"   - Non-null count: {df[nist_col].notna().sum()}/{len(df)}")
                    print(f"   - Sample values: {df[nist_col].dropna().head(5).tolist()}")
                    
                    # Check value ranges
                    numeric_values = pd.to_numeric(df[nist_col], errors='coerce').dropna()
                    if len(numeric_values) > 0:
                        print(f"   - Min: {numeric_values.min():.6f}")
                        print(f"   - Max: {numeric_values.max():.6f}")
                        print(f"   - Mean: {numeric_values.mean():.6f}")
            
            # Pattern analysis
            print("\n🔍 NIST column pattern analysis:")
            patterns = {}
            for col in nist_columns:
                # Extract pattern like "NIST_5601-5700 (1)"
                col_str = str(col)
                if '_' in col_str and '(' in col_str:
                    base_pattern = col_str.split('(')[0].strip()
                    if base_pattern not in patterns:
                        patterns[base_pattern] = []
                    patterns[base_pattern].append(col_str)
            
            for pattern, cols in patterns.items():
                print(f"\n   Pattern: '{pattern}'")
                print(f"   Columns: {len(cols)}")
                for col in cols:
                    print(f"     - {col}")
            
            # Check if there are any sample Excel files to cross-reference
            print("\n📁 Looking for sample Excel files...")
            excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and f != ratio_file]
            for excel_file in excel_files[:5]:
                print(f"   - {excel_file}")
            
            return {
                'total_columns': len(df.columns),
                'nist_columns': nist_columns,
                'patterns': patterns,
                'compound_column': compound_col,
                'shape': df.shape
            }
            
        else:
            print(f"❌ Ratio-database.xlsx not found at: {ratio_file}")
            return None
            
    except Exception as e:
        print(f"❌ Error analyzing Ratio database: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    analyze_nist_columns()