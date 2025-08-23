#!/usr/bin/env python3

"""
FIXED RATIO PREVIEW SERVICE
Correctly uses:
- Area Compound data from uploaded Excel file 
- Sample Index data from DATABASE
- Compound Index data from DATABASE
"""

import pandas as pd
import numpy as np
import os
import tempfile
from io import BytesIO
import json

def generate_ratio_preview_table(excel_file_path, max_compounds=50, max_samples=10):
    """
    Generate ratio preview using uploaded Excel + database reference data
    """
    
    print("🎯 GENERATING RATIO PREVIEW TABLE (FIXED VERSION)")
    print("=" * 70)
    
    try:
        # Import database models
        from models import SampleIndex, CompoundIndex
        
        # Step 1: Load ONLY the Area Compound data from uploaded Excel
        print("📊 LOADING AREA COMPOUND DATA FROM EXCEL...")
        all_sheets = pd.read_excel(excel_file_path, sheet_name=None)
        available_sheet_names = list(all_sheets.keys())
        print(f"📋 Available sheets: {available_sheet_names}")
        
        # Use the first sheet (should be the Area Compound data)
        main_sheet_name = available_sheet_names[0]
        area_data = all_sheets[main_sheet_name]
        print(f"✅ Loaded Area Compound data from '{main_sheet_name}': {area_data.shape}")
        
        # Step 2: Load Sample Index data from DATABASE
        print("🗄️ LOADING SAMPLE INDEX FROM DATABASE...")
        sample_nist_mapping = SampleIndex.get_sample_mapping()
        print(f"✅ Loaded {len(sample_nist_mapping)} sample mappings from database")
        
        # Show sample mapping examples
        sample_examples = dict(list(sample_nist_mapping.items())[:5])
        print(f"📋 Sample mapping examples: {sample_examples}")
        
        # Step 3: Load Compound Index data from DATABASE
        print("🗄️ LOADING COMPOUND INDEX FROM DATABASE...")
        compound_records = CompoundIndex.query.all()
        compound_istd_mapping = {record.compound: record.istd for record in compound_records}
        print(f"✅ Loaded {len(compound_istd_mapping)} compound mappings from database")
        
        # Show compound mapping examples  
        compound_examples = dict(list(compound_istd_mapping.items())[:5])
        print(f"📋 Compound mapping examples: {compound_examples}")
        
        # Step 4: Process Area Compound data structure and skip headers
        print("🔍 ANALYZING AREA COMPOUND DATA STRUCTURE...")
        
        # Check for header rows that need to be skipped
        print(f"🔍 First few rows of data:")
        for i in range(min(3, len(area_data))):
            print(f"  Row {i}: {list(area_data.iloc[i, :5])}")
        
        # Detect and skip header rows
        skip_rows = 0
        compound_col = area_data.columns[0]
        
        # Check if first few rows contain header-like values
        for i in range(min(3, len(area_data))):
            first_val = str(area_data.iloc[i, 0]).strip().lower()
            if first_val in ['name', 'area', 'compound', 'analyte']:
                skip_rows = i + 1
                print(f"🔍 Found header row at position {i}: '{area_data.iloc[i, 0]}', will skip {skip_rows} rows")
        
        if skip_rows == 0:
            print("🔍 No header rows detected, using all data")
        
        # Extract actual compound data after skipping headers
        compounds = area_data.iloc[skip_rows:][compound_col].dropna().astype(str).str.strip()
        print(f"✅ Extracted {len(compounds)} compounds after skipping {skip_rows} header rows")
        
        # Find sample and NIST columns in the uploaded data
        sample_columns = [col for col in area_data.columns[1:] if 'PH-HC_' in str(col)]
        nist_columns = [col for col in area_data.columns[1:] if 'NIST' in str(col)]
        
        print(f"✅ Found {len(compounds)} compounds, {len(sample_columns)} samples, {len(nist_columns)} NIST columns")
        print(f"📊 Sample columns: {sample_columns[:5]}...")
        print(f"📊 NIST columns: {nist_columns}")
        
        # Step 5: Create corrected sample-to-NIST mapping using database logic
        print("🔗 MAPPING UPLOADED SAMPLES TO DATABASE REFERENCES...")
        
        # The uploaded samples (PH-HC_5601, etc.) need to be mapped to database samples (PH-HC_1, etc.)
        # Then use database to get NIST mapping
        corrected_sample_nist_map = {}
        
        for i, actual_sample in enumerate(sample_columns):
            # Extract sample number from uploaded sample name
            if 'PH-HC_' in actual_sample:
                try:
                    sample_num = int(actual_sample.split('_')[1])  # e.g., 5601 from PH-HC_5601
                    
                    # Calculate position within 100-sample range (1-100)
                    range_start = (sample_num // 100) * 100 + 1  # e.g., 5601 for PH-HC_5601
                    position_in_range = sample_num - range_start + 1  # Position 1-100
                    
                    # Create database sample name
                    database_sample = f"PH-HC_{position_in_range}"  # e.g., PH-HC_1
                    
                    # Get NIST mapping from database
                    nist_column_pattern = sample_nist_mapping.get(database_sample)
                    
                    if nist_column_pattern:
                        # Find matching NIST column in uploaded data
                        matching_nist_col = None
                        for nist_col in nist_columns:
                            # Match pattern: NIST_1-100(1) → NIST_5601-5700(1) 
                            if '(1)' in nist_column_pattern and '(1)' in str(nist_col):
                                matching_nist_col = nist_col
                                break
                            elif '(2)' in nist_column_pattern and '(2)' in str(nist_col):
                                matching_nist_col = nist_col
                                break
                            elif '(3)' in nist_column_pattern and '(3)' in str(nist_col):
                                matching_nist_col = nist_col
                                break
                            elif '(4)' in nist_column_pattern and '(4)' in str(nist_col):
                                matching_nist_col = nist_col
                                break
                        
                        corrected_sample_nist_map[actual_sample] = matching_nist_col
                        
                        if i < 5:  # Show first few mappings
                            print(f"  📍 {actual_sample} → {database_sample} → {nist_column_pattern} → {matching_nist_col}")
                    
                except (ValueError, IndexError) as e:
                    print(f"⚠️ Could not parse sample {actual_sample}: {e}")
        
        print(f"✅ Created {len(corrected_sample_nist_map)} corrected sample mappings")
        
        # Step 6: Select compounds and samples for preview
        print("🎯 SELECTING COMPOUNDS AND SAMPLES FOR PREVIEW...")
        
        # Prioritize key AcylCarnitine compounds
        key_compounds = [
            'AcylCarnitine 10:0', 'AcylCarnitine 12:0', 'AcylCarnitine 12:1', 
            'AcylCarnitine 14:0', 'AcylCarnitine 16:0', 'AcylCarnitine 18:0',
            'AcylCarnitine 18:1', 'AcylCarnitine 20:0'
        ]
        
        # Find available compounds (adjust indices for skipped rows)
        available_compounds = []
        compound_indices = {}
        
        for key_compound in key_compounds:
            for idx, compound in enumerate(compounds):
                if key_compound in str(compound):
                    available_compounds.append(key_compound)
                    # Adjust index to account for skipped header rows
                    compound_indices[key_compound] = idx + skip_rows
                    break
            if len(available_compounds) >= max_compounds:
                break
        
        # Add more compounds if needed
        if len(available_compounds) < max_compounds:
            for idx, compound in enumerate(compounds):
                compound_name = str(compound).strip()
                if compound_name not in available_compounds and compound_name != 'nan' and compound_name:
                    available_compounds.append(compound_name)
                    # Adjust index to account for skipped header rows
                    compound_indices[compound_name] = idx + skip_rows
                    if len(available_compounds) >= max_compounds:
                        break
        
        # Select samples
        selected_samples = sample_columns[:max_samples]
        
        print(f"📊 Selected {len(available_compounds)} compounds, {len(selected_samples)} samples for preview")
        
        # Step 7: Generate comprehensive ratio calculations
        print("🧮 CALCULATING RATIOS...")
        preview_data = []
        full_data = []
        
        for compound_name in available_compounds:
            compound_idx = compound_indices[compound_name]
            
            # Get ISTD from database
            istd_name = compound_istd_mapping.get(compound_name, 'LPC 18:1 d7')  # Default fallback
            
            # Find ISTD index in uploaded data (adjust for skipped rows)
            istd_idx = None
            for idx, comp in enumerate(compounds):
                if istd_name in str(comp):
                    istd_idx = idx + skip_rows  # Adjust for skipped header rows
                    break
            
            if istd_idx is None:
                print(f"⚠️ ISTD '{istd_name}' not found for {compound_name}, skipping...")
                continue
            
            for sample_col in selected_samples:
                # Get compound and ISTD areas from uploaded Excel
                compound_area = area_data.iloc[compound_idx][sample_col]
                istd_area = area_data.iloc[istd_idx][sample_col]
                
                # Calculate sample ratio with enhanced error checking
                sample_ratio = None
                compound_area_float = 0
                istd_area_float = 0
                
                try:
                    if pd.notna(compound_area) and pd.notna(istd_area):
                        # Convert to float and check for valid numbers
                        compound_area_float = float(compound_area)
                        istd_area_float = float(istd_area)
                        
                        if istd_area_float != 0:
                            sample_ratio = compound_area_float / istd_area_float
                except (ValueError, TypeError) as e:
                    print(f"⚠️ Invalid area data for {compound_name} in {sample_col}: compound={compound_area}, istd={istd_area}")
                    continue
                
                # Get NIST column from corrected mapping
                nist_column = corrected_sample_nist_map.get(sample_col)
                nist_ratio = None
                nist_result = None
                nist_compound_area_float = 0
                nist_istd_area_float = 0
                
                if nist_column:
                    nist_compound_area = area_data.iloc[compound_idx][nist_column]
                    nist_istd_area = area_data.iloc[istd_idx][nist_column]
                    
                    try:
                        if pd.notna(nist_compound_area) and pd.notna(nist_istd_area):
                            # Convert to float with error checking
                            nist_compound_area_float = float(nist_compound_area)
                            nist_istd_area_float = float(nist_istd_area)
                            
                            if nist_istd_area_float != 0:
                                nist_ratio = nist_compound_area_float / nist_istd_area_float
                                
                                if sample_ratio is not None and nist_ratio != 0:
                                    nist_result = sample_ratio / nist_ratio
                    except (ValueError, TypeError) as e:
                        print(f"⚠️ Invalid NIST area data for {compound_name} in {nist_column}: compound={nist_compound_area}, istd={nist_istd_area}")
                        nist_compound_area_float = 0
                        nist_istd_area_float = 0
                else:
                    nist_compound_area_float = 0
                    nist_istd_area_float = 0
                
                # Create preview row
                preview_row = {
                    'Compound': compound_name,
                    'ISTD': istd_name,
                    'Sample': sample_col,
                    'NIST_Column': nist_column or 'N/A',
                    'Sample_Ratio': f"{sample_ratio:.6f}" if sample_ratio is not None else 'N/A',
                    'NIST_Ratio': f"{nist_ratio:.6f}" if nist_ratio is not None else 'N/A',
                    'NIST_Result': f"{nist_result:.4f}" if nist_result is not None else 'N/A'
                }
                
                # Create full data row using processed float values
                full_row = {
                    'Compound': compound_name,
                    'ISTD': istd_name,
                    'Sample': sample_col,
                    'NIST_Column': nist_column or 'N/A',
                    'Sample_Compound_Area': int(compound_area_float) if compound_area_float > 0 else 0,
                    'Sample_ISTD_Area': int(istd_area_float) if istd_area_float > 0 else 0,
                    'Sample_Ratio': sample_ratio if sample_ratio is not None else 0,
                    'NIST_Compound_Area': int(nist_compound_area_float) if nist_compound_area_float > 0 else 0,
                    'NIST_ISTD_Area': int(nist_istd_area_float) if nist_istd_area_float > 0 else 0,
                    'NIST_Ratio': nist_ratio if nist_ratio is not None else 0,
                    'NIST_Result': nist_result if nist_result is not None else 0,
                    'Data_Source': 'Excel + Database',
                    'Calculation_Method': 'Sample_Ratio ÷ NIST_Ratio'
                }
                
                preview_data.append(preview_row)
                full_data.append(full_row)
        
        # Step 8: Create summary statistics
        valid_nist_results = [float(row['NIST_Result']) for row in preview_data if row['NIST_Result'] != 'N/A']
        
        summary_stats = {
            'total_calculations': len(preview_data),
            'valid_results': len(valid_nist_results),
            'compounds_analyzed': len(available_compounds),
            'samples_analyzed': len(selected_samples),
            'avg_nist_result': round(np.mean(valid_nist_results), 4) if valid_nist_results else 0,
            'nist_columns_used': len(set([row['NIST_Column'] for row in preview_data if row['NIST_Column'] != 'N/A'])),
            'data_sources': 'Excel (Area) + Database (Sample/Compound Index)',
            'database_samples': len(sample_nist_mapping),
            'database_compounds': len(compound_istd_mapping)
        }
        
        print(f"✅ Generated {len(preview_data)} ratio calculations")
        print(f"✅ {len(valid_nist_results)} valid NIST results")
        
        return {
            'success': True,
            'preview_data': preview_data,
            'full_data': full_data,
            'summary_stats': summary_stats,
            'compounds': available_compounds,
            'samples': selected_samples,
            'nist_columns': nist_columns,
            'method': 'excel_plus_database'
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
    """Export full ratio data to Excel file with multiple sheets"""
    
    try:
        df = pd.DataFrame(full_data)
        
        # Create BytesIO buffer
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Main data sheet
            df.to_excel(writer, sheet_name='Ratio_Calculations', index=False)
            
            # Summary sheet
            if full_data:
                summary_data = {
                    'Metric': [
                        'Total Calculations',
                        'Valid NIST Results', 
                        'Unique Compounds',
                        'Unique Samples',
                        'Average NIST Result',
                        'Data Source Method',
                        'Formula Used'
                    ],
                    'Value': [
                        len(full_data),
                        len([row for row in full_data if row['NIST_Result'] != 0]),
                        len(set([row['Compound'] for row in full_data])),
                        len(set([row['Sample'] for row in full_data])),
                        f"{np.mean([row['NIST_Result'] for row in full_data if row['NIST_Result'] != 0]):.6f}",
                        'Excel (Area Data) + Database (Sample/Compound Index)',
                        'Sample Ratio ÷ NIST Ratio'
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Analysis_Summary', index=False)
        
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