#!/usr/bin/env python3
"""
STREAMLINED METABOLOMICS CALCULATION SERVICE
Complete recreation based on user specifications
Single input file → 3-step calculation → 2-sheet output + preview
"""

import pandas as pd
import numpy as np
import json
from io import BytesIO
import tempfile
import os
import uuid
from datetime import datetime
from models import db, CompoundIndex

class StreamlinedCalculatorService:
    """Professional metabolomics calculator with 3-step formula"""
    
    def __init__(self):
        self.ratio_database = self._load_ratio_database()
        self.sample_index = self._load_sample_index()
        self.compound_index = self._load_compound_index()
        
    def _load_ratio_database(self):
        """Load NIST ratio standards from Ratio-database.xlsx"""
        try:
            # Try multiple possible locations
            possible_paths = [
                "/mnt/c/Users/T14/Desktop/metabolomics-project/Ratio-database.xlsx",
                "/mnt/c/Users/T14/Desktop/Ratio-database.xlsx",
                "Ratio-database.xlsx",
                "./Ratio-database.xlsx"
            ]
            
            for ratio_file in possible_paths:
                if os.path.exists(ratio_file):
                    df = pd.read_excel(ratio_file)
                    print(f"✅ Loaded Ratio database from {ratio_file}: {df.shape[0]} entries")
                    print(f"   Columns: {list(df.columns)}")
                    return df
            
            print("⚠️ Ratio-database.xlsx not found in any location, using fallback")
            return None
        except Exception as e:
            print(f"⚠️ Error loading Ratio database: {e}")
            return None
    
    def _load_sample_index(self):
        """Load sample index mapping from sample-index.xlsx"""
        try:
            possible_paths = [
                "/mnt/c/Users/T14/Desktop/metabolomics-project/sample-index.xlsx",
                "/mnt/c/Users/T14/Desktop/sample-index.xlsx",
                "sample-index.xlsx",
                "./sample-index.xlsx"
            ]
            
            for sample_file in possible_paths:
                if os.path.exists(sample_file):
                    df = pd.read_excel(sample_file)
                    print(f"✅ Loaded Sample index from {sample_file}: {df.shape[0]} entries")
                    return df
            
            print("⚠️ sample-index.xlsx not found in any location, using dynamic mapping")
            return None
        except Exception as e:
            print(f"⚠️ Error loading Sample index: {e}")
            return None
    
    def _load_compound_index(self):
        """Load compound index with ISTD mappings from compound-index.xlsx"""
        try:
            possible_paths = [
                "/mnt/c/Users/T14/Desktop/metabolomics-project/compound-index.xlsx",
                "/mnt/c/Users/T14/Desktop/compound-index.xlsx",
                "compound-index.xlsx",
                "./compound-index.xlsx"
            ]
            
            for compound_file in possible_paths:
                if os.path.exists(compound_file):
                    df = pd.read_excel(compound_file)
                    print(f"✅ Loaded Compound index from {compound_file}: {df.shape[0]} entries")
                    return df
            
            print("⚠️ compound-index.xlsx not found in any location, trying database")
            # Fallback to database
            try:
                compounds = CompoundIndex.query.all()
                data = []
                for comp in compounds:
                    data.append({
                        'Compound': comp.compound,
                        'istd': comp.istd,
                        'conc_nm': comp.conc_nm,
                        'response_factor': comp.response_factor
                    })
                df = pd.DataFrame(data) if data else None
                if df is not None:
                    print(f"✅ Loaded {len(data)} compounds from database")
                return df
            except:
                print("⚠️ Database not accessible, using defaults")
                return None
        except Exception as e:
            print(f"⚠️ Error loading Compound index: {e}")
            return None

    def determine_sample_numbering(self, sample_columns):
        """
        Determine sample numbering based on user specification:
        PH-HC_5600-5700 → NIST_5600-5700(1), NIST_5600-5700(2), etc.
        PH-HC_1-100 → NIST_1-100(1), NIST_1-100(2), etc.
        """
        print(f"🔍 Analyzing sample columns: {len(sample_columns)} samples")
        
        # Extract sample numbers from PH-HC_XXXX format
        sample_numbers = []
        for col in sample_columns:
            try:
                if 'PH-HC_' in str(col):
                    num_str = str(col).replace('PH-HC_', '')
                    if num_str.isdigit():
                        sample_numbers.append(int(num_str))
            except:
                continue
        
        if not sample_numbers:
            print("⚠️ No valid PH-HC_ samples found, using default numbering")
            return {
                'base_number': 1,
                'sample_range': '1-100',
                'nist_patterns': ['NIST_1-100 (1)', 'NIST_1-100 (2)', 'NIST_1-100 (3)', 'NIST_1-100 (4)']
            }
        
        sample_numbers.sort()
        min_sample = min(sample_numbers)
        max_sample = max(sample_numbers)
        
        # Determine base numbering (round to nearest hundred)
        base_hundred = (min_sample // 100) * 100
        if base_hundred == 0:
            base_hundred = 1
        
        # For ranges like 5701-5800, we want to use 5700-5799 or 5701-5800
        end_hundred = base_hundred + 99
        
        # Special case for ranges that start at x01 (like 5701)
        if min_sample % 100 == 1:  # Starts at x01
            base_hundred = min_sample  # Use 5701 as base
            end_hundred = ((min_sample // 100) + 1) * 100  # Use 5800 as end
            
        # Adjust if max sample exceeds our calculated end
        if max_sample > end_hundred:
            end_hundred = max_sample
        
        sample_range = f"{base_hundred}-{end_hundred}"
        nist_patterns = [
            f"NIST_{sample_range} (1)",
            f"NIST_{sample_range} (2)", 
            f"NIST_{sample_range} (3)",
            f"NIST_{sample_range} (4)"
        ]
        
        print(f"📊 Sample numbering determined:")
        print(f"   Base range: {sample_range}")
        print(f"   NIST patterns: {nist_patterns}")
        
        return {
            'base_number': base_hundred,
            'sample_range': sample_range,
            'nist_patterns': nist_patterns,
            'actual_range': f"{min_sample}-{max_sample}"
        }

    def get_nist_ratio(self, substance, nist_pattern):
        """Get NIST ratio for substance from ratio database"""
        if self.ratio_database is None:
            # Fallback to database values
            try:
                compound = CompoundIndex.query.filter_by(compound=substance).first()
                if compound:
                    return compound.nist_standard
            except:
                pass
            return 0.1769  # Ultimate fallback
        
        try:
            # Look for substance in ratio database
            substance_row = self.ratio_database[self.ratio_database['Compound'] == substance]
            if not substance_row.empty:
                # Try to find the specific NIST pattern column
                for col in self.ratio_database.columns:
                    if nist_pattern in str(col) or str(col) in nist_pattern:
                        value = substance_row.iloc[0][col]
                        if pd.notna(value) and value != 0:
                            return float(value)
                
                # If specific pattern not found, use first numeric column after Compound
                numeric_cols = self.ratio_database.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    if col != 'Compound':
                        value = substance_row.iloc[0][col]
                        if pd.notna(value) and value != 0:
                            return float(value)
            
            print(f"⚠️ NIST ratio not found for {substance} in {nist_pattern}, using fallback")
            return 0.1769
            
        except Exception as e:
            print(f"⚠️ Error getting NIST ratio for {substance}: {e}")
            return 0.1769

    def get_compound_info(self, substance):
        """Get compound information (ISTD, concentration, response factor)"""
        if self.compound_index is None:
            return {
                'istd': 'LPC 18:1 d7',
                'conc_nm': 90.029,
                'response_factor': 1.0
            }
        
        try:
            compound_row = self.compound_index[self.compound_index['Compound'] == substance]
            if not compound_row.empty:
                return {
                    'istd': compound_row.iloc[0].get('istd', 'LPC 18:1 d7'),
                    'conc_nm': float(compound_row.iloc[0].get('conc_nm', 90.029)),
                    'response_factor': float(compound_row.iloc[0].get('response_factor', 1.0))
                }
            else:
                print(f"⚠️ Compound info not found for {substance}, using defaults")
                return {
                    'istd': 'LPC 18:1 d7',
                    'conc_nm': 90.029,
                    'response_factor': 1.0
                }
        except Exception as e:
            print(f"⚠️ Error getting compound info for {substance}: {e}")
            return {
                'istd': 'LPC 18:1 d7',
                'conc_nm': 90.029,
                'response_factor': 1.0
            }

    def debug_excel_structure(self, area_file):
        """Debug function to analyze Excel file structure"""
        try:
            area_data = pd.read_excel(area_file)
            print(f"🔍 EXCEL DEBUG INFO:")
            print(f"   Shape: {area_data.shape}")
            print(f"   Columns: {list(area_data.columns)}")
            print(f"   First 3 rows:")
            print(area_data.head(3).to_string())
            
            # Look for potential compound column
            compound_candidates = []
            for col in area_data.columns:
                col_name = str(col).lower()
                if any(keyword in col_name for keyword in ['compound', 'substance', 'lipid', 'metabolite']):
                    compound_candidates.append(col)
            
            print(f"   Potential compound columns: {compound_candidates}")
            
            # Look for sample columns
            sample_candidates = [col for col in area_data.columns if 'PH-HC' in str(col)]
            print(f"   Sample columns found: {len(sample_candidates)}")
            if sample_candidates:
                print(f"   Sample examples: {sample_candidates[:5]}")
            
            return {
                'columns': list(area_data.columns),
                'shape': area_data.shape,
                'compound_candidates': compound_candidates,
                'sample_candidates': sample_candidates,
                'first_rows': area_data.head(3).to_dict('records')
            }
            
        except Exception as e:
            print(f"❌ Debug error: {e}")
            return {'error': str(e)}

    def calculate_streamlined(self, area_file, coefficient=500):
        """
        Main calculation function with 3-step formula:
        1. Ratio = Substance Area ÷ ISTD Area
        2. NIST = Substance Ratio ÷ NIST Standard Ratio
        3. Agilent = Ratio × Conc.(nM) × Response Factor × Coefficient
        """
        print(f"🚀 STREAMLINED CALCULATION STARTED")
        print(f"   Coefficient: {coefficient}")
        
        try:
            # Read area compound data
            area_data = pd.read_excel(area_file)
            print(f"📊 Loaded area data: {area_data.shape}")
            print(f"📋 Columns found: {list(area_data.columns)}")
            
            # Smart column detection - look for compound column
            compound_column = None
            for col in area_data.columns:
                col_name = str(col).lower()
                if any(keyword in col_name for keyword in ['compound', 'substance', 'lipid', 'metabolite']):
                    compound_column = col
                    break
            
            # If no obvious compound column, use first column
            if compound_column is None:
                compound_column = area_data.columns[0]
                print(f"⚠️ No obvious compound column found, using first column: '{compound_column}'")
            else:
                print(f"✅ Found compound column: '{compound_column}'")
            
            # Check if compound column has valid data
            if compound_column not in area_data.columns:
                raise ValueError(f"Selected compound column '{compound_column}' not found in file")
            
            # Use the detected compound column
            substances = area_data[compound_column].dropna().tolist()
            sample_columns = [col for col in area_data.columns 
                            if col != compound_column and 'PH-HC' in str(col)]
            
            # Sort sample columns numerically (not alphabetically)
            def extract_sample_number(col_name):
                try:
                    if 'PH-HC_' in str(col_name):
                        num_str = str(col_name).replace('PH-HC_', '')
                        return int(num_str)
                    return 999999  # Put non-numeric at end
                except:
                    return 999999
            
            sample_columns = sorted(sample_columns, key=extract_sample_number)
            
            print(f"🧬 Found {len(substances)} substances")
            print(f"🔬 Found {len(sample_columns)} samples")
            print(f"📋 Sample columns (sorted): {sample_columns[:10]}...")  # Show first 10
            
            # Determine sample numbering
            numbering_info = self.determine_sample_numbering(sample_columns)
            
            # Initialize results
            nist_results = []
            agilent_results = []
            detailed_calculations = {}  # Store detailed calculation breakdowns
            
            # Process each substance
            for i, substance in enumerate(substances):
                print(f"🧪 Processing substance {i+1}/{len(substances)}: {substance}")
                
                # Get compound information
                compound_info = self.get_compound_info(substance)
                istd_name = compound_info['istd']
                
                # Get NIST ratio for this substance (using first NIST pattern)
                nist_pattern = numbering_info['nist_patterns'][0]
                nist_ratio = self.get_nist_ratio(substance, nist_pattern)
                
                substance_nist_row = {'Substance': substance}
                substance_agilent_row = {'Substance': substance}
                
                # Process each sample
                for sample_col in sample_columns:
                    calculation_key = f"{substance}_{sample_col}"
                    
                    try:
                        # Get substance area
                        substance_area_raw = area_data.loc[i, sample_col]
                        substance_area = float(substance_area_raw) if pd.notna(substance_area_raw) else 0.0
                        
                        # Find ISTD area (look for ISTD in the same data)
                        istd_area = 0.0
                        istd_found = False
                        istd_row_index = -1
                        
                        for j, comp_name in enumerate(substances):
                            if istd_name in str(comp_name):
                                istd_area_raw = area_data.loc[j, sample_col]
                                istd_area = float(istd_area_raw) if pd.notna(istd_area_raw) else 0.0
                                istd_found = True
                                istd_row_index = j
                                break
                        
                        if istd_area == 0:
                            istd_area = 1.0  # Avoid division by zero
                        
                        # STEP 1: Calculate Ratio
                        ratio = substance_area / istd_area
                        
                        # STEP 2: Calculate NIST
                        nist_result = ratio / nist_ratio if nist_ratio != 0 else 0.0
                        
                        # STEP 3: Calculate Agilent
                        agilent_result = (ratio * 
                                        compound_info['conc_nm'] * 
                                        compound_info['response_factor'] * 
                                        coefficient)
                        
                        # Store detailed calculation breakdown
                        detailed_calculations[calculation_key] = {
                            # Basic Info
                            'substance': substance,
                            'sample': sample_col,
                            'substance_index': i + 1,
                            
                            # Source Data
                            'source_data': {
                                'substance_area_raw': substance_area_raw,
                                'substance_area': substance_area,
                                'istd_area_raw': area_data.loc[istd_row_index, sample_col] if istd_found else 'NOT FOUND',
                                'istd_area': istd_area,
                                'istd_found': istd_found,
                                'istd_row_index': istd_row_index + 1 if istd_found else -1
                            },
                            
                            # Database References
                            'database_info': {
                                'istd_name': istd_name,
                                'nist_pattern': nist_pattern,
                                'nist_standard': nist_ratio,
                                'concentration_nm': compound_info['conc_nm'],
                                'response_factor': compound_info['response_factor'],
                                'coefficient': coefficient
                            },
                            
                            # Step-by-Step Calculations
                            'calculations': {
                                'step_1_ratio': {
                                    'formula': 'Substance Area ÷ ISTD Area',
                                    'calculation': f"{substance_area} ÷ {istd_area}",
                                    'result': ratio
                                },
                                'step_2_nist': {
                                    'formula': 'Substance Ratio ÷ NIST Standard',
                                    'calculation': f"{ratio} ÷ {nist_ratio}",
                                    'result': nist_result
                                },
                                'step_3_agilent': {
                                    'formula': 'Ratio × Conc.(nM) × Response Factor × Coefficient',
                                    'calculation': f"{ratio} × {compound_info['conc_nm']} × {compound_info['response_factor']} × {coefficient}",
                                    'result': agilent_result
                                }
                            },
                            
                            # Final Results
                            'final_results': {
                                'ratio': ratio,
                                'nist_result': nist_result,
                                'agilent_result': agilent_result
                            }
                        }
                        
                        # Store results
                        substance_nist_row[sample_col] = nist_result
                        substance_agilent_row[sample_col] = agilent_result
                        
                    except Exception as e:
                        print(f"⚠️ Error processing {substance} in {sample_col}: {e}")
                        substance_nist_row[sample_col] = 0.0
                        substance_agilent_row[sample_col] = 0.0
                        
                        # Store error details
                        detailed_calculations[calculation_key] = {
                            'substance': substance,
                            'sample': sample_col,
                            'error': str(e),
                            'final_results': {
                                'ratio': 0.0,
                                'nist_result': 0.0,
                                'agilent_result': 0.0
                            }
                        }
                
                nist_results.append(substance_nist_row)
                agilent_results.append(substance_agilent_row)
            
            # Convert to DataFrames
            nist_df = pd.DataFrame(nist_results)
            agilent_df = pd.DataFrame(agilent_results)
            
            # Ensure column order: Substance first, then samples in numerical order
            if len(nist_df.columns) > 1:
                column_order = ['Substance'] + sample_columns
                # Only reorder columns that actually exist in the DataFrame
                existing_columns = [col for col in column_order if col in nist_df.columns]
                nist_df = nist_df[existing_columns]
                agilent_df = agilent_df[existing_columns]
            
            print(f"✅ Calculation completed")
            print(f"   NIST results: {nist_df.shape}")
            print(f"   Agilent results: {agilent_df.shape}")
            print(f"   Column order: {list(nist_df.columns)[:10]}...")  # Show first 10 columns
            
            return {
                'nist_data': nist_df,
                'agilent_data': agilent_df,
                'detailed_calculations': detailed_calculations,
                'numbering_info': numbering_info,
                'substance_count': len(substances),
                'sample_count': len(sample_columns)
            }
            
        except Exception as e:
            print(f"❌ Calculation error: {e}")
            raise e

    def create_excel_output(self, nist_data, agilent_data, filename_base="metabolomics_results"):
        """Create Excel file with 2 sheets: NIST Results and Agilent Results"""
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write NIST Results sheet
            nist_data.to_excel(writer, sheet_name='NIST Results', index=False)
            
            # Write Agilent Results sheet  
            agilent_data.to_excel(writer, sheet_name='Agilent Results', index=False)
            
            # Format sheets
            workbook = writer.book
            
            # Format NIST sheet
            nist_sheet = workbook['NIST Results']
            nist_sheet.sheet_properties.tabColor = "0066CC"
            
            # Format Agilent sheet
            agilent_sheet = workbook['Agilent Results']
            agilent_sheet.sheet_properties.tabColor = "FF6600"
        
        output.seek(0)
        return output

    def save_temp_results(self, nist_data, agilent_data, detailed_calculations=None):
        """Save results to temporary file and return session info"""
        try:
            session_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"streamlined_results_{timestamp}.xlsx"
            
            # Create temp directory for this session
            temp_dir = tempfile.gettempdir()
            session_dir = os.path.join(temp_dir, f"streamlined_{session_id}")
            os.makedirs(session_dir, exist_ok=True)
            
            # Save Excel file
            excel_path = os.path.join(session_dir, filename)
            excel_output = self.create_excel_output(nist_data, agilent_data, filename)
            
            with open(excel_path, 'wb') as f:
                f.write(excel_output.getvalue())
            
            # Save detailed calculations as JSON
            if detailed_calculations:
                details_path = os.path.join(session_dir, f"details_{session_id}.json")
                with open(details_path, 'w') as f:
                    # Convert numpy types to native Python types for JSON serialization
                    json_safe_details = {}
                    for key, value in detailed_calculations.items():
                        json_safe_details[key] = self._make_json_safe(value)
                    
                    json.dump(json_safe_details, f, indent=2)
                print(f"💾 Detailed calculations saved: {details_path}")
            
            print(f"💾 Results saved to session: {session_dir}")
            
            return {
                'session_id': session_id,
                'filename': filename,
                'temp_path': excel_path,
                'session_dir': session_dir
            }
            
        except Exception as e:
            print(f"❌ Error saving temp results: {e}")
            raise e

    def _make_json_safe(self, obj):
        """Convert numpy types and other non-JSON-serializable types to JSON-safe types"""
        if isinstance(obj, dict):
            return {k: self._make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_safe(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        else:
            return obj

    def get_calculation_details(self, session_id, substance, sample):
        """Get detailed calculation breakdown for a specific substance-sample combination"""
        try:
            temp_dir = tempfile.gettempdir()
            session_dir = os.path.join(temp_dir, f"streamlined_{session_id}")
            details_path = os.path.join(session_dir, f"details_{session_id}.json")
            
            if not os.path.exists(details_path):
                return {'error': 'Calculation details not found'}
            
            with open(details_path, 'r') as f:
                all_details = json.load(f)
            
            calculation_key = f"{substance}_{sample}"
            
            if calculation_key in all_details:
                return all_details[calculation_key]
            else:
                return {'error': f'Details not found for {substance} in {sample}'}
                
        except Exception as e:
            print(f"❌ Error getting calculation details: {e}")
            return {'error': str(e)}

# Global instance
streamlined_calculator = StreamlinedCalculatorService()