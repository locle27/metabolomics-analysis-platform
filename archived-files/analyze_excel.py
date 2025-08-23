#!/usr/bin/env python3

import pandas as pd
import sys

def analyze_excel_file():
    try:
        file_path = 'Calculate alysis.xlsx'
        
        # Read all sheet names
        excel_file = pd.ExcelFile(file_path)
        print("Sheet names:")
        for sheet in excel_file.sheet_names:
            print(f"  - {sheet}")
        
        # Analyze each sheet
        for sheet_name in excel_file.sheet_names:
            print(f"\n=== {sheet_name} ===")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("First 5 rows:")
            print(df.head())
            print("---")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_excel_file()