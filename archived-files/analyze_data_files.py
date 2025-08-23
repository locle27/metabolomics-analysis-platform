#!/usr/bin/env python3
"""
ULTRA ANALYSIS OF DATA FILES
Analyze all 4 Excel files to understand data structure for complete recreation
"""

import pandas as pd
import os

def analyze_excel_file(file_path, file_name):
    """Analyze an Excel file and print detailed information"""
    print(f"\n{'='*80}")
    print(f"📊 ANALYZING: {file_name}")
    print(f"{'='*80}")
    
    if not os.path.exists(file_path):
        print(f"❌ FILE NOT FOUND: {file_path}")
        return None
    
    try:
        # Get all sheet names
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        print(f"📋 SHEETS FOUND ({len(sheet_names)}): {sheet_names}")
        
        data = {}
        for sheet_name in sheet_names:
            print(f"\n📄 SHEET: {sheet_name}")
            print("-" * 50)
            
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            data[sheet_name] = df
            
            print(f"📏 DIMENSIONS: {df.shape} (rows × columns)")
            print(f"📝 COLUMNS ({len(df.columns)}): {list(df.columns)}")
            
            # Show first few rows
            print(f"\n🔍 FIRST 5 ROWS:")
            print(df.head().to_string())
            
            # Show data types
            print(f"\n📊 DATA TYPES:")
            print(df.dtypes.to_string())
            
            # Show sample data for key columns
            if len(df) > 0:
                print(f"\n💡 SAMPLE DATA:")
                for col in df.columns[:5]:  # Show first 5 columns
                    sample_values = df[col].dropna().head(3).tolist()
                    print(f"  {col}: {sample_values}")
            
            print(f"\n📈 SUMMARY STATS:")
            if df.select_dtypes(include=['number']).shape[1] > 0:
                print(df.describe().to_string())
            else:
                print("  No numeric columns for summary statistics")
        
        return data
        
    except Exception as e:
        print(f"❌ ERROR READING {file_name}: {str(e)}")
        return None

def main():
    """Main analysis function"""
    print("🚀 ULTRA ANALYSIS: METABOLOMICS DATA FILES")
    print("🎯 Understanding data structure for complete system recreation\n")
    
    # Define file paths
    files_to_analyze = [
        ("area-compound.xlsx", "MAIN INPUT FILE - Compound Areas"),
        ("Ratio-database.xlsx", "NIST RATIO STANDARDS DATABASE"), 
        ("sample-index.xlsx", "SAMPLE INDEX MAPPING"),
        ("compound-index.xlsx", "COMPOUND INDEX WITH ISTD MAPPINGS")
    ]
    
    base_path = "/mnt/c/Users/T14/Desktop/metabolomics-project/"
    
    all_data = {}
    
    for filename, description in files_to_analyze:
        file_path = os.path.join(base_path, filename)
        print(f"\n🎯 {description}")
        data = analyze_excel_file(file_path, filename)
        if data:
            all_data[filename] = data
    
    # Final summary
    print(f"\n{'='*80}")
    print("📋 COMPLETE ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    for filename, data in all_data.items():
        if data:
            print(f"\n📁 {filename}:")
            for sheet_name, df in data.items():
                print(f"  └── {sheet_name}: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # Identify key patterns
    print(f"\n🔍 KEY PATTERNS IDENTIFIED:")
    
    # Check for sample naming patterns
    for filename, data in all_data.items():
        if data and 'area-compound.xlsx' in filename:
            for sheet_name, df in data.items():
                sample_cols = [col for col in df.columns if 'PH-HC' in str(col)]
                if sample_cols:
                    print(f"  📊 Sample columns in {filename}: {len(sample_cols)} samples")
                    print(f"      First few: {sample_cols[:5]}")
                    
                    # Extract sample numbers
                    sample_numbers = []
                    for col in sample_cols:
                        try:
                            if 'PH-HC_' in str(col):
                                num = str(col).replace('PH-HC_', '')
                                if num.isdigit():
                                    sample_numbers.append(int(num))
                        except:
                            pass
                    
                    if sample_numbers:
                        sample_numbers.sort()
                        print(f"      Sample range: {min(sample_numbers)} to {max(sample_numbers)}")
    
    # Check for compound patterns
    for filename, data in all_data.items():
        if data:
            for sheet_name, df in data.items():
                if 'Compound' in df.columns:
                    compounds = df['Compound'].dropna().head(10).tolist()
                    print(f"  🧬 Compounds in {filename}/{sheet_name}: {len(df)} total")
                    print(f"      Examples: {compounds}")
                
                # Check for ISTD patterns
                if 'istd' in df.columns or 'ISTD' in df.columns:
                    istd_col = 'istd' if 'istd' in df.columns else 'ISTD'
                    istds = df[istd_col].dropna().unique()[:5]
                    print(f"  🎯 ISTD patterns in {filename}/{sheet_name}: {list(istds)}")

if __name__ == "__main__":
    main()