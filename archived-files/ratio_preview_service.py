#!/usr/bin/env python3

"""
RATIO PREVIEW SERVICE
Service for generating comprehensive ratio calculation previews with download functionality
"""

import pandas as pd
import numpy as np
import os
import tempfile
from io import BytesIO
import json

def generate_ratio_preview_table(excel_file_path, max_compounds=50, max_samples=10):
    """
    Generate a comprehensive ratio preview table from Excel file
    Returns both display data and full data for download
    """
    
    print("🎯 GENERATING RATIO PREVIEW TABLE")
    print("=" * 60)
    
    try:
        # First, discover what sheets are available in the Excel file
        print("🔍 Discovering available sheets in Excel file...")
        all_sheets = pd.read_excel(excel_file_path, sheet_name=None)
        available_sheet_names = list(all_sheets.keys())
        print(f"📊 Available sheets: {available_sheet_names}")
        
        # Find the main data sheet (contains PH-HC samples)
        main_sheet_name = None
        for sheet_name in available_sheet_names:
            if 'PH-HC' in str(sheet_name) or any('PH-HC' in str(col) for col in all_sheets[sheet_name].columns):
                main_sheet_name = sheet_name
                print(f"✅ Found main data sheet: {sheet_name}")
                break
        
        if not main_sheet_name:
            # Fallback: use first sheet if no PH-HC found
            main_sheet_name = available_sheet_names[0]
            print(f"⚠️ No PH-HC sheet found, using first sheet: {main_sheet_name}")
        
        # Load all required sheets with dynamic names
        area_data = all_sheets[main_sheet_name]
        
        # Find Sample Index sheet
        sample_index_sheet = None
        for sheet_name in available_sheet_names:
            if 'sample' in str(sheet_name).lower() and 'index' in str(sheet_name).lower():
                sample_index_sheet = sheet_name
                break
        
        if sample_index_sheet:
            sample_index = all_sheets[sample_index_sheet]
            print(f"✅ Found Sample Index sheet: {sample_index_sheet}")
        else:
            print("⚠️ No Sample Index sheet found")
            return {
                'success': False,
                'error': 'Sample Index sheet not found',
                'preview_data': [],
                'full_data': [],
                'summary_stats': {}
            }
        
        # Find Compound Index sheet
        compound_index_sheet = None
        for sheet_name in available_sheet_names:
            if 'compound' in str(sheet_name).lower() and 'index' in str(sheet_name).lower():
                compound_index_sheet = sheet_name
                break
        
        if compound_index_sheet:
            compound_index = all_sheets[compound_index_sheet]
            print(f"✅ Found Compound Index sheet: {compound_index_sheet}")
        else:
            print("⚠️ No Compound Index sheet found")
            return {
                'success': False,
                'error': 'Compound Index sheet not found',
                'preview_data': [],
                'full_data': [],
                'summary_stats': {}
            }
        
        print(f"✅ Loaded Excel data - Main: {area_data.shape}, Sample Index: {sample_index.shape}, Compound Index: {compound_index.shape}")
        
        # Get structure info
        compound_col = area_data.columns[0]
        compounds = area_data[compound_col].dropna().astype(str).str.strip()
        
        # Find columns
        sample_columns = [col for col in area_data.columns[1:] if 'PH-HC_' in str(col)]
        nist_columns = [col for col in area_data.columns[1:] if 'NIST' in str(col)]
        
        # Build compound → ISTD mapping
        compound_istd_map = {}
        comp_col = compound_index.columns[0]
        istd_col = compound_index.columns[1]
        
        for _, row in compound_index.iterrows():
            compound_name = str(row[comp_col]).strip()
            istd_name = str(row[istd_col]).strip()
            compound_istd_map[compound_name] = istd_name
        
        # Create corrected sample-to-NIST mapping
        sample_index_nist = sample_index.iloc[:, 1].tolist()
        corrected_sample_nist_map = {}
        
        for i, actual_sample in enumerate(sample_columns):
            if i < len(sample_index_nist):
                nist_from_index = sample_index_nist[i]
                
                # Find matching NIST column in actual data
                for nist_col in nist_columns:
                    if '(1)' in nist_from_index and '(1)' in str(nist_col):
                        corrected_sample_nist_map[actual_sample] = nist_col
                        break
                    elif '(2)' in nist_from_index and '(2)' in str(nist_col):
                        corrected_sample_nist_map[actual_sample] = nist_col
                        break
                    elif '(3)' in nist_from_index and '(3)' in str(nist_col):
                        corrected_sample_nist_map[actual_sample] = nist_col
                        break
                    elif '(4)' in nist_from_index and '(4)' in str(nist_col):
                        corrected_sample_nist_map[actual_sample] = nist_col
                        break
        
        # Select compounds and samples for preview
        key_compounds = [
            'AcylCarnitine 10:0', 'AcylCarnitine 12:0', 'AcylCarnitine 12:1', 
            'AcylCarnitine 14:0', 'AcylCarnitine 16:0', 'AcylCarnitine 18:0',
            'AcylCarnitine 18:1', 'AcylCarnitine 20:0'
        ]
        
        # Find available compounds from key list
        available_compounds = []
        compound_indices = {}
        
        for key_compound in key_compounds:
            for idx, compound in enumerate(compounds):
                if key_compound in str(compound):
                    available_compounds.append(key_compound)
                    compound_indices[key_compound] = idx
                    break
            if len(available_compounds) >= max_compounds:
                break
        
        # If still need more compounds, add others
        if len(available_compounds) < max_compounds:
            for idx, compound in enumerate(compounds):
                compound_name = str(compound).strip()
                if compound_name not in available_compounds and compound_name != 'nan':
                    available_compounds.append(compound_name)
                    compound_indices[compound_name] = idx
                    if len(available_compounds) >= max_compounds:
                        break
        
        # Select samples (first N samples)
        selected_samples = sample_columns[:max_samples]
        
        print(f"📊 Processing {len(available_compounds)} compounds, {len(selected_samples)} samples")
        
        # Generate comprehensive ratio data
        preview_data = []
        full_data = []  # For complete download
        
        for compound_name in available_compounds:
            compound_idx = compound_indices[compound_name]
            
            # Get ISTD
            istd_name = compound_istd_map.get(compound_name, 'LPC 18:1 d7')
            
            # Find ISTD index
            istd_idx = None
            for idx, comp in enumerate(compounds):
                if istd_name in str(comp):
                    istd_idx = idx
                    break
            
            if istd_idx is None:
                continue
            
            for sample_col in selected_samples:
                # Get areas
                compound_area = area_data.iloc[compound_idx][sample_col]
                istd_area = area_data.iloc[istd_idx][sample_col]
                
                # Calculate sample ratio
                sample_ratio = None
                if pd.notna(compound_area) and pd.notna(istd_area) and istd_area != 0:
                    sample_ratio = float(compound_area) / float(istd_area)
                
                # Get NIST column and ratio
                nist_column = corrected_sample_nist_map.get(sample_col)
                nist_ratio = None
                nist_result = None
                
                if nist_column:
                    nist_compound_area = area_data.iloc[compound_idx][nist_column]
                    nist_istd_area = area_data.iloc[istd_idx][nist_column]
                    
                    if pd.notna(nist_compound_area) and pd.notna(nist_istd_area) and nist_istd_area != 0:
                        nist_ratio = float(nist_compound_area) / float(nist_istd_area)
                        
                        if sample_ratio is not None and nist_ratio != 0:
                            nist_result = sample_ratio / nist_ratio
                
                # Create row for preview (limited data)
                preview_row = {
                    'Compound': compound_name,
                    'ISTD': istd_name,
                    'Sample': sample_col,
                    'NIST_Column': nist_column or 'N/A',
                    'Sample_Ratio': f"{sample_ratio:.6f}" if sample_ratio is not None else 'N/A',
                    'NIST_Ratio': f"{nist_ratio:.6f}" if nist_ratio is not None else 'N/A',
                    'NIST_Result': f"{nist_result:.4f}" if nist_result is not None else 'N/A'
                }
                
                # Create row for full download (all data)
                full_row = {
                    'Compound': compound_name,
                    'ISTD': istd_name,
                    'Sample': sample_col,
                    'NIST_Column': nist_column or 'N/A',
                    'Sample_Compound_Area': int(compound_area) if pd.notna(compound_area) else 0,
                    'Sample_ISTD_Area': int(istd_area) if pd.notna(istd_area) else 0,
                    'Sample_Ratio': sample_ratio if sample_ratio is not None else 0,
                    'NIST_Compound_Area': int(nist_compound_area) if pd.notna(nist_compound_area) else 0,
                    'NIST_ISTD_Area': int(nist_istd_area) if pd.notna(nist_istd_area) else 0,
                    'NIST_Ratio': nist_ratio if nist_ratio is not None else 0,
                    'NIST_Result': nist_result if nist_result is not None else 0,
                    'Calculation_Formula': f'({sample_ratio:.6f} ÷ {nist_ratio:.6f})' if (sample_ratio and nist_ratio) else 'N/A'
                }
                
                preview_data.append(preview_row)
                full_data.append(full_row)
        
        # Create summary statistics
        valid_nist_results = [float(row['NIST_Result']) for row in preview_data if row['NIST_Result'] != 'N/A']
        
        summary_stats = {
            'total_calculations': len(preview_data),
            'valid_results': len(valid_nist_results),
            'compounds_analyzed': len(available_compounds),
            'samples_analyzed': len(selected_samples),
            'avg_nist_result': np.mean(valid_nist_results) if valid_nist_results else 0,
            'nist_columns_used': len(set([row['NIST_Column'] for row in preview_data if row['NIST_Column'] != 'N/A']))
        }
        
        return {
            'success': True,
            'preview_data': preview_data,
            'full_data': full_data,
            'summary_stats': summary_stats,
            'compounds': available_compounds,
            'samples': selected_samples,
            'nist_columns': nist_columns
        }
        
    except Exception as e:
        print(f"❌ Error generating ratio preview: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'preview_data': [],
            'full_data': [],
            'summary_stats': {}
        }

def export_to_excel(full_data, filename="ratio_preview_export.xlsx"):
    """Export full ratio data to Excel file"""
    
    try:
        df = pd.DataFrame(full_data)
        
        # Create BytesIO buffer for in-memory Excel file
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Main data sheet
            df.to_excel(writer, sheet_name='Ratio_Calculations', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Total Calculations', 
                    'Valid Results', 
                    'Compounds Analyzed',
                    'Samples Analyzed',
                    'Average NIST Result'
                ],
                'Value': [
                    len(full_data),
                    len([row for row in full_data if row['NIST_Result'] != 0]),
                    len(set([row['Compound'] for row in full_data])),
                    len(set([row['Sample'] for row in full_data])),
                    f"{np.mean([row['NIST_Result'] for row in full_data if row['NIST_Result'] != 0]):.4f}"
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        buffer.seek(0)
        return buffer, filename
        
    except Exception as e:
        print(f"❌ Error exporting to Excel: {e}")
        return None, None

def export_to_csv(full_data, filename="ratio_preview_export.csv"):
    """Export full ratio data to CSV file"""
    
    try:
        df = pd.DataFrame(full_data)
        
        # Create CSV in memory
        buffer = BytesIO()
        csv_data = df.to_csv(index=False)
        buffer.write(csv_data.encode('utf-8'))
        buffer.seek(0)
        
        return buffer, filename
        
    except Exception as e:
        print(f"❌ Error exporting to CSV: {e}")
        return None, None