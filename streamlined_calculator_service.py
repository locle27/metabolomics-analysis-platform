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
        
        # Create normalized compound mapping for fast lookups
        self._compound_name_map = self._create_compound_name_map()
        
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
                        'ISTD': comp.istd,  # Updated to match corrected Excel format
                        'Conc. (nM)': comp.conc_nm,  # Updated to match corrected Excel format
                        'Response factor': comp.response_factor  # Updated to match corrected Excel format
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
    
    def _normalize_compound_name(self, compound_name):
        """
        Ultra-comprehensive lipid name normalization for complex chemical notation:
        - Handles fatty acid notation (16:0, 20:4, etc.)
        - Complex nested structures like 22:5(n3)/20:1
        - Mixed bracket types: [], (), {}
        - Lipid class prefixes: (O-), (P-), etc.
        - Position indicators: [a], [b], [sn1], [sn2]
        - Multiple separators: /, -, space
        """
        if not compound_name or pd.isna(compound_name):
            return [""]
        
        import re
        name = str(compound_name).strip()
        variations = [name]
        
        # === STEP 1: Generate bracket variations ===
        bracket_variations = []
        
        # Simple bracket swaps: [a] ↔ (a)
        simple_brackets = ['a', 'b', 'c', 'd', 'e', 'sn1', 'sn2', 'n3', 'n6']
        for bracket_content in simple_brackets:
            for variant in variations[:]:  # Copy to avoid modification during iteration
                # Square to round
                if f'[{bracket_content}]' in variant:
                    bracket_variations.append(variant.replace(f'[{bracket_content}]', f'({bracket_content})'))
                # Round to square
                if f'({bracket_content})' in variant:
                    bracket_variations.append(variant.replace(f'({bracket_content})', f'[{bracket_content}]'))
        
        # Complex bracket patterns with regex
        for variant in variations[:]:
            # Convert ALL square brackets to parentheses: [anything] → (anything)
            square_to_paren = re.sub(r'\[([^\]]+)\]', r'(\1)', variant)
            if square_to_paren != variant:
                bracket_variations.append(square_to_paren)
            
            # Convert ALL parentheses to square brackets: (anything) → [anything]
            # But be careful with fatty acid notation like 22:5(n3)
            paren_to_square = re.sub(r'\(([^)]+)\)', r'[\1]', variant)
            if paren_to_square != variant:
                bracket_variations.append(paren_to_square)
        
        variations.extend(bracket_variations)
        
        # === STEP 2: Handle lipid class prefixes ===
        prefix_variations = []
        lipid_prefixes = ['O-', 'P-', 'e-', 'p-']  # Common ether/plasmalogen prefixes
        
        for variant in variations[:]:
            for prefix in lipid_prefixes:
                # Try different bracket types for prefixes
                patterns_to_try = [
                    (f'({prefix}', f'[{prefix}'),    # (O- → [O-
                    (f'[{prefix}', f'({prefix}'),    # [O- → (O-
                    (f'{prefix}', f'({prefix}'),     # O- → (O-
                    (f'{prefix}', f'[{prefix}'),     # O- → [O-
                ]
                
                for old_pattern, new_pattern in patterns_to_try:
                    if old_pattern in variant:
                        new_variant = variant.replace(old_pattern, new_pattern)
                        if new_variant != variant:
                            prefix_variations.append(new_variant)
        
        variations.extend(prefix_variations)
        
        # === STEP 3: Normalize fatty acid notation and spacing ===
        fatty_acid_variations = []
        for variant in variations[:]:
            # Normalize spacing around separators
            normalized = variant
            
            # Normalize colons (fatty acid notation: 16:0, 20:4)
            normalized = re.sub(r'\s*:\s*', ':', normalized)
            
            # Normalize hyphens
            normalized = re.sub(r'\s*-\s*', '-', normalized)
            
            # Normalize slashes
            normalized = re.sub(r'\s*/\s*', '/', normalized)
            
            # Normalize spaces around brackets
            normalized = re.sub(r'\s*\[\s*', '[', normalized)
            normalized = re.sub(r'\s*\]\s*', ']', normalized)
            normalized = re.sub(r'\s*\(\s*', '(', normalized)
            normalized = re.sub(r'\s*\)\s*', ')', normalized)
            
            # Normalize multiple spaces
            normalized = re.sub(r'\s+', ' ', normalized)
            normalized = normalized.strip()
            
            if normalized != variant:
                fatty_acid_variations.append(normalized)
        
        variations.extend(fatty_acid_variations)
        
        # === STEP 4: Handle separator variations ===
        separator_variations = []
        for variant in variations[:]:
            # Try space vs no space around separators
            space_variants = [
                # Spaces around separators
                variant.replace('/', ' / ').replace('-', ' - '),
                # No spaces around separators  
                variant.replace(' / ', '/').replace(' - ', '-'),
                # Mixed patterns
                variant.replace(' /', '/').replace('/ ', '/'),
                variant.replace(' -', '-').replace('- ', '-'),
            ]
            
            # CRITICAL: Handle forward slash vs backslash variations
            # Many databases use \ while input files use /
            slash_variants = [
                variant.replace('/', '\\'),  # Forward to backslash
                variant.replace('\\', '/'),  # Backslash to forward
                # With spaces
                variant.replace('/', ' \\ ').replace(' \\ ', '\\'),
                variant.replace('\\', ' / ').replace(' / ', '/'),
            ]
            
            all_separator_variants = space_variants + slash_variants
            
            for sep_var in all_separator_variants:
                # Clean up multiple spaces
                cleaned = re.sub(r'\s+', ' ', sep_var.strip())
                if cleaned != variant and cleaned:
                    separator_variations.append(cleaned)
        
        variations.extend(separator_variations)
        
        # === STEP 5: Handle nested parentheses patterns ===
        # For cases like 22:5(n3) within larger brackets
        nested_variations = []
        for variant in variations[:]:
            # Try converting nested parentheses patterns
            # Example: [a-18:0 22:5(n3)/20:1 20:4] might have variants with different nesting
            
            # Find patterns like X:Y(nZ) and try bracket variations
            nested_pattern = r'(\d+:\d+)\(([^)]+)\)'
            matches = re.findall(nested_pattern, variant)
            
            for fatty_acid, nested_content in matches:
                original_pattern = f'{fatty_acid}({nested_content})'
                bracket_pattern = f'{fatty_acid}[{nested_content}]'
                
                new_variant = variant.replace(original_pattern, bracket_pattern)
                if new_variant != variant:
                    nested_variations.append(new_variant)
        
        variations.extend(nested_variations)
        
        # === STEP 6: Clean up and deduplicate ===
        final_variations = []
        seen = set()
        
        for variant in variations:
            if variant and variant not in seen:
                seen.add(variant)
                final_variations.append(variant)
        
        return final_variations
    
    def _clean_area_values(self, raw_values):
        """
        Clean and convert area values to numeric floats, handling:
        - String values like 'N/A', 'NA', '', 'NULL', 'NaN'
        - Non-numeric text values
        - Missing values (NaN, None)
        - Invalid number formats
        - Excel column headers (reduced logging)
        """
        cleaned_values = []
        
        for value in raw_values:
            try:
                # Handle None and NaN
                if value is None or pd.isna(value):
                    cleaned_values.append(0.0)
                    continue
                
                # Convert to string for processing
                str_value = str(value).strip()
                
                # Handle common string representations of missing/invalid data
                if str_value.upper() in ['N/A', 'NA', 'NULL', 'NAN', '', '#N/A', '#VALUE!', '#REF!', '#DIV/0!']:
                    cleaned_values.append(0.0)
                    continue
                
                # SPECIAL: Handle common Excel headers silently (reduce log spam)
                if str_value.upper() in ['AREA', 'NAME', 'COMPOUND', 'SUBSTANCE']:
                    cleaned_values.append(0.0)
                    continue
                
                # Try to convert to float
                numeric_value = float(str_value)
                
                # Handle negative values (shouldn't exist in area data)
                if numeric_value < 0:
                    cleaned_values.append(0.0)
                else:
                    cleaned_values.append(numeric_value)
                    
            except (ValueError, TypeError, OverflowError):
                # If conversion fails, default to 0.0 (only log non-header values)
                str_val = str(value).strip()
                if str_val.upper() not in ['AREA', 'NAME', 'COMPOUND', 'SUBSTANCE']:
                    print(f"⚠️ Invalid area value '{value}' converted to 0.0")
                cleaned_values.append(0.0)
        
        return np.array(cleaned_values, dtype=float)
    
    def _create_compound_name_map(self):
        """Create a mapping of normalized compound names to original database entries"""
        compound_map = {}
        
        if self.compound_index is None:
            return compound_map
        
        print("🔄 Creating normalized compound name mapping...")
        
        for idx, row in self.compound_index.iterrows():
            compound_name = row.get('Compound', '')
            if pd.isna(compound_name) or not compound_name:
                continue
                
            # Get all normalized variations
            variations = self._normalize_compound_name(compound_name)
            
            # Map all variations to the original row
            for variation in variations:
                if variation and variation not in compound_map:
                    # ⚡ ENHANCED: Handle both old and new column formats for flexibility
                    istd_value = row.get('ISTD') or row.get('istd', 'LPC 18:1 d7')
                    conc_value = row.get('Conc. (nM)') or row.get('conc_nm', 90.029)
                    response_value = row.get('Response factor') or row.get('response_factor', 1.0)
                    
                    # Safely convert to float with fallback
                    try:
                        conc_float = float(conc_value) if pd.notna(conc_value) else 90.029
                    except (ValueError, TypeError):
                        conc_float = 90.029
                    
                    try:
                        response_float = float(response_value) if pd.notna(response_value) else 1.0
                    except (ValueError, TypeError):
                        response_float = 1.0
                    
                    compound_map[variation] = {
                        'original_name': compound_name,
                        'istd': istd_value,
                        'conc_nm': conc_float,
                        'response_factor': response_float
                    }
        
        print(f"📊 Created {len(compound_map)} normalized compound mappings")
        return compound_map

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

    def find_matching_nist_column(self, ph_hc_sample, nist_columns):
        """
        Find the correct NIST column that matches a PH-HC sample.
        Intelligently matches based on sample number ranges.
        
        Examples:
        PH-HC_6 → NIST_1-100 (1) [if 6 is in range 1-100]
        PH-HC_5701 → NIST_5701-5800 (1) [if 5701 is in range 5701-5800]
        """
        if not nist_columns:
            return None
            
        # Extract sample number from PH-HC column
        try:
            if 'PH-HC_' not in str(ph_hc_sample):
                return None
                
            sample_num_str = str(ph_hc_sample).replace('PH-HC_', '')
            if not sample_num_str.isdigit():
                return None
                
            sample_num = int(sample_num_str)
            
            # Find matching NIST column based on range
            best_match = None
            best_score = -1
            
            for nist_col in nist_columns:
                nist_str = str(nist_col)
                
                # Try to extract range from NIST column name
                # Examples: NIST_1-100 (1), NIST_5701-5800 (2), etc.
                if 'NIST_' in nist_str:
                    try:
                        # Extract the range part (between NIST_ and space or parenthesis)
                        range_part = nist_str.replace('NIST_', '').split(' ')[0].split('(')[0]
                        
                        if '-' in range_part:
                            range_start, range_end = range_part.split('-')
                            range_start = int(range_start)
                            range_end = int(range_end)
                            
                            # Check if sample number falls within this range
                            if range_start <= sample_num <= range_end:
                                # Calculate score based on how well it fits
                                range_size = range_end - range_start + 1
                                score = 1000 - range_size  # Prefer smaller, more specific ranges
                                
                                if score > best_score:
                                    best_score = score
                                    best_match = nist_col
                                    
                    except (ValueError, IndexError) as e:
                        continue
            
            if best_match:
                print(f"🎯 Matched {ph_hc_sample} → {best_match} (sample {sample_num})")
                return best_match
            else:
                # Fallback: use first NIST column if no range match
                fallback = nist_columns[0]
                print(f"⚠️ No range match for {ph_hc_sample} (sample {sample_num}), using fallback: {fallback}")
                return fallback
                
        except Exception as e:
            print(f"⚠️ Error matching NIST column for {ph_hc_sample}: {e}")
            return nist_columns[0] if nist_columns else None

    def analyze_nist_column_ranges(self, nist_columns):
        """Analyze and display NIST column ranges for debugging"""
        if not nist_columns:
            print("📊 No NIST columns to analyze")
            return
            
        print("📊 NIST Column Range Analysis:")
        ranges_found = {}
        
        for nist_col in nist_columns:
            nist_str = str(nist_col)
            if 'NIST_' in nist_str:
                try:
                    # Extract range part
                    range_part = nist_str.replace('NIST_', '').split(' ')[0].split('(')[0]
                    if '-' in range_part:
                        range_start, range_end = range_part.split('-')
                        range_key = f"{range_start}-{range_end}"
                        
                        if range_key not in ranges_found:
                            ranges_found[range_key] = []
                        ranges_found[range_key].append(nist_col)
                        
                except (ValueError, IndexError):
                    print(f"   ⚠️ Could not parse range from: {nist_col}")
        
        for range_key, columns in ranges_found.items():
            print(f"   📈 Range {range_key}: {len(columns)} columns ({columns[:2]}...)")
        
        print(f"   💡 Total ranges detected: {len(ranges_found)}")

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
            # First try exact match (fastest)
            compound_row = self.compound_index[self.compound_index['Compound'] == substance]
            if not compound_row.empty:
                return {
                    'istd': compound_row.iloc[0].get('istd', 'LPC 18:1 d7'),
                    'conc_nm': float(compound_row.iloc[0].get('conc_nm', 90.029)),
                    'response_factor': float(compound_row.iloc[0].get('response_factor', 1.0))
                }
            
            # Try normalized compound name mapping
            if hasattr(self, '_compound_name_map') and self._compound_name_map:
                # Check if substance exists in normalized mapping
                if substance in self._compound_name_map:
                    compound_info = self._compound_name_map[substance]
                    print(f"✅ Found normalized match: '{substance}' → '{compound_info['original_name']}'")
                    return compound_info
                
                # Try all variations of the input substance name
                substance_variations = self._normalize_compound_name(substance)
                for variant in substance_variations:
                    if variant in self._compound_name_map:
                        compound_info = self._compound_name_map[variant]
                        print(f"✅ Found variant match: '{substance}' (as '{variant}') → '{compound_info['original_name']}'")
                        return compound_info
            
            # If still no match, use defaults
            variations_tried = self._normalize_compound_name(substance)
            print(f"⚠️ Compound '{substance}' not found in database after trying {len(variations_tried)} variations, using fallback defaults")
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
            # ⚡ ULTRA ENHANCED: Multi-step Excel analysis with robust header detection
            print("🔍 Performing comprehensive Excel file analysis...")
            
            # First read to detect full structure
            raw_df = pd.read_excel(area_file, header=None)
            print(f"📋 Raw Excel shape: {raw_df.shape}")
            print(f"📋 First few cells in column 0: {[raw_df.iloc[i, 0] for i in range(min(8, len(raw_df)))]}")
            
            # STEP 1: Find the actual header row (look for PH-HC patterns)
            header_row = 0
            data_start_row = 1
            
            print("🔎 Analyzing potential header rows...")
            for row_idx in range(min(15, len(raw_df))):
                row_values = [str(val) for val in raw_df.iloc[row_idx].tolist()]
                ph_hc_count = sum(1 for val in row_values if 'PH-HC' in str(val))
                nist_count = sum(1 for val in row_values if 'NIST' in str(val))
                
                print(f"   Row {row_idx}: PH-HC columns={ph_hc_count}, NIST columns={nist_count}, First cell='{raw_df.iloc[row_idx, 0]}'")
                
                # If this row has multiple PH-HC patterns, it's likely the header
                if ph_hc_count >= 2:  # Need at least 2 PH-HC columns to be a proper header
                    header_row = row_idx
                    data_start_row = row_idx + 1  # Data starts in the next row
                    print(f"✅ Detected header row at index {header_row}, data starts at {data_start_row}")
                    break
            
            # STEP 2: Read with proper header
            area_data = pd.read_excel(area_file, header=header_row)
            print(f"📊 Loaded area data with header at row {header_row}: {area_data.shape}")
            print(f"📋 Columns found: {list(area_data.columns)[:10]}...")
            
            # STEP 3: Critical adjustment - remove header row data contamination
            # Since pandas includes the header row in the data, we need to adjust indices
            first_data_value = area_data.iloc[0, 0] if not area_data.empty else "N/A"
            print(f"🔍 First data row, first cell: '{first_data_value}'")
            
            # If first row still contains header-like data, skip it
            skip_rows = 0
            if str(first_data_value).strip() in ['Name', 'Compound', 'Substance', 'Method', 'Chemical']:
                skip_rows = 1
                print(f"⚠️ Skipping first data row as it contains header artifacts")
            
            # Apply skip if needed
            if skip_rows > 0:
                area_data = area_data.iloc[skip_rows:].reset_index(drop=True)
                print(f"📊 After skipping {skip_rows} rows: {area_data.shape}")
                new_first_value = area_data.iloc[0, 0] if not area_data.empty else "N/A"
                print(f"🔍 New first data row, first cell: '{new_first_value}'")
            
            # STEP 4: Enhanced data validation
            
            # Smart column detection - look for compound column
            compound_column = None
            for col in area_data.columns:
                col_name = str(col).lower()
                if any(keyword in col_name for keyword in ['compound', 'substance', 'lipid', 'metabolite', 'method']):
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
            raw_substances = area_data[compound_column].dropna().tolist()
            
            # ⚡ ULTRA ENHANCED: Robust compound filtering with detailed validation
            header_keywords = ['Name', 'Compound', 'Substance', 'Chemical', 'Area', 'Sample', 'Method', 'Compound Method', 'nan']
            substances = []
            filtered_items = []
            
            print(f"🔬 Processing {len(raw_substances)} potential compounds...")
            
            for idx, substance in enumerate(raw_substances):
                if pd.isna(substance) or substance is None:
                    continue
                    
                substance_str = str(substance).strip()
                
                # Enhanced validation criteria
                is_valid_compound = (
                    substance_str and  # Not empty
                    substance_str not in header_keywords and  # Not a known header
                    len(substance_str) > 3 and  # Reasonable length
                    not substance_str.upper() in ['AREA', 'NAME', 'COMPOUND', 'METHOD', 'NAN', 'NULL'] and  # Not header variants
                    not substance_str.lower() in ['area', 'name', 'compound', 'method', 'nan', 'null'] and  # Case variations
                    # Real compounds usually contain numbers, colons (fatty acids), or specific lipid patterns
                    (any(char.isdigit() for char in substance_str) or 
                     ':' in substance_str or  # Fatty acid notation like 16:0
                     any(pattern in substance_str for pattern in ['PC', 'LPC', 'TG', 'AcylCarnitine', 'PE', 'PS', 'SM', 'Cer', 'DG']))
                )
                
                if is_valid_compound:
                    substances.append(substance_str)
                else:
                    # Track what we filtered for debugging
                    if substance_str and len(substance_str) > 1:  # Only log non-empty items
                        filtered_items.append(f"Row{idx}: '{substance_str}'")
            
            # Show filtering results
            if filtered_items:
                print(f"⚠️ Filtered {len(filtered_items)} non-compound entries:")
                for item in filtered_items[:10]:  # Show first 10
                    print(f"   {item}")
                if len(filtered_items) > 10:
                    print(f"   ... and {len(filtered_items) - 10} more")
            
            print(f"✅ Extracted {len(substances)} valid compounds from {len(raw_substances)} entries")
            
            sample_columns = [col for col in area_data.columns 
                            if col != compound_column and 'PH-HC' in str(col)]
            
            # Also detect NIST columns for the new ratio calculation
            nist_columns = [col for col in area_data.columns
                           if col != compound_column and 'NIST' in str(col)]
            
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
            
            # Sort NIST columns for consistent ordering
            nist_columns = sorted(nist_columns)
            
            print(f"🧬 Found {len(substances)} substances")
            print(f"🔬 Found {len(sample_columns)} PH-HC samples")
            print(f"📋 Sample columns (sorted): {sample_columns[:10]}...")  # Show first 10
            print(f"🧪 Found {len(nist_columns)} NIST columns: {nist_columns[:5]}...")  # Show first 5
            
            # ⚡ ULTRA ENHANCED DIAGNOSTIC: Deep analysis of AcylCarnitine 10:0 data extraction
            print(f"\n🔬 COMPREHENSIVE DIAGNOSTIC FOR AcylCarnitine 10:0:")
            
            if 'AcylCarnitine 10:0' in substances:
                acyl_index = substances.index('AcylCarnitine 10:0')
                print(f"✅ AcylCarnitine 10:0 found at compound index {acyl_index}")
                print(f"   DataFrame row index (after header adjustment): {acyl_index}")
                
                # Show the actual Excel row being accessed
                actual_excel_row = header_row + 1 + skip_rows + acyl_index
                print(f"   Actual Excel file row: {actual_excel_row}")
                
                # Check the raw compound name in that row
                actual_compound_name = area_data.iloc[acyl_index][compound_column]
                print(f"   Actual compound name in DataFrame: '{actual_compound_name}'")
                
                # Deep dive into area values with enhanced diagnostic
                print(f"   📊 Detailed area analysis for first 3 samples:")
                for idx, col in enumerate(sample_columns[:3]):
                    if col in area_data.columns:
                        raw_area_val = area_data.iloc[acyl_index][col]
                        cleaned_area_val = self._clean_area_values([raw_area_val])[0]
                        
                        # Enhanced diagnostic info
                        val_type = type(raw_area_val).__name__
                        is_numeric = isinstance(raw_area_val, (int, float, np.number))
                        print(f"      {col}: raw='{raw_area_val}' (type={val_type}, numeric={is_numeric}) → cleaned={cleaned_area_val}")
                        
                        # Critical check for string contamination
                        if isinstance(raw_area_val, str) and raw_area_val.strip().upper() == 'AREA':
                            print(f"      ❌ FOUND HEADER CONTAMINATION: Raw value is 'Area' string!")
                            print(f"         This indicates row indexing is still incorrect.")
                            
                            # Try to find the correct data by looking a few rows down
                            for offset in range(1, 5):
                                try:
                                    test_row = acyl_index + offset
                                    if test_row < len(area_data):
                                        test_val = area_data.iloc[test_row][col]
                                        if isinstance(test_val, (int, float, np.number)):
                                            print(f"         Potential correct data found {offset} rows down: {test_val}")
                                            break
                                except:
                                    continue
                
                # Enhanced ISTD checking
                istd_candidates = [s for s in substances if 'LPC' in s and 'd7' in s]
                print(f"   🧪 ISTD Analysis:")
                print(f"      Available LPC d7 compounds: {istd_candidates[:5]}")
                
                if 'LPC 18:1 d7' in substances:
                    istd_index = substances.index('LPC 18:1 d7')
                    print(f"      ✅ ISTD (LPC 18:1 d7) found at index {istd_index}")
                    
                    # Deep ISTD diagnostic
                    for idx, col in enumerate(sample_columns[:3]):
                        if col in area_data.columns:
                            istd_raw = area_data.iloc[istd_index][col]
                            istd_cleaned = self._clean_area_values([istd_raw])[0]
                            istd_type = type(istd_raw).__name__
                            print(f"      {col}: ISTD raw='{istd_raw}' (type={istd_type}) → cleaned={istd_cleaned}")
                else:
                    print(f"      ❌ Exact ISTD 'LPC 18:1 d7' not found!")
                    if istd_candidates:
                        closest_istd = istd_candidates[0]
                        print(f"      Using closest match: '{closest_istd}'")
                    
            else:
                print(f"❌ AcylCarnitine 10:0 NOT FOUND in substances list!")
                # Enhanced compound searching
                acyl_patterns = ['AcylCarnitine', 'Acyl', 'Carnitine', '10:0']
                print(f"   🔍 Searching for related patterns in {len(substances)} substances:")
                
                for pattern in acyl_patterns:
                    matches = [s for s in substances if pattern in s][:5]
                    if matches:
                        print(f"      Pattern '{pattern}': {matches}")
                    else:
                        print(f"      Pattern '{pattern}': No matches")
                
                # Show first 20 substances for reference
                print(f"   📋 First 20 substances found: {substances[:20]}")
            
            print(f"")  # Blank line for readability
            self.analyze_nist_column_ranges(nist_columns)
            
            # Determine sample numbering
            numbering_info = self.determine_sample_numbering(sample_columns)
            
            # 🚀 PERFORMANCE OPTIMIZATION: Pre-compute mappings to avoid O(n²) complexity
            print("⚡ Optimizing performance - pre-computing mappings...")
            
            # Pre-compute ISTD index mappings to avoid nested loops
            istd_index_map = {}
            compound_info_map = {}
            
            for i, substance in enumerate(substances):
                compound_info = self.get_compound_info(substance)
                compound_info_map[substance] = compound_info
                istd_name = compound_info['istd']
                
                # Find ISTD index once for this substance
                for j, comp_name in enumerate(substances):
                    if istd_name in str(comp_name):
                        istd_index_map[substance] = j
                        break
                else:
                    istd_index_map[substance] = -1  # ISTD not found
            
            # Pre-compute NIST column mappings for all PH-HC samples
            nist_mapping_cache = {}
            for sample_col in sample_columns:
                nist_mapping_cache[sample_col] = self.find_matching_nist_column(sample_col, nist_columns)
            
            print(f"⚡ Optimizations complete - {len(istd_index_map)} ISTD mappings, {len(nist_mapping_cache)} NIST mappings cached")
            
            # Convert DataFrame to numpy for faster access
            area_values = area_data.select_dtypes(include=[np.number]).values
            numeric_columns = area_data.select_dtypes(include=[np.number]).columns.tolist()
            
            # Create column index mappings for fast lookup
            col_to_idx = {col: idx for idx, col in enumerate(area_data.columns)}
            
            # Initialize results
            nist_results = []
            agilent_results = []
            nist_ratio_results = []  # New: for NIST ratio calculations
            detailed_calculations = {}  # Store detailed calculation breakdowns (only when needed)
            
            # Process each substance (optimized)
            for i, substance in enumerate(substances):
                if i % 100 == 0:  # Reduce logging frequency for performance
                    print(f"⚡ Processing substances {i+1}-{min(i+100, len(substances))}/{len(substances)}")
                
                # Get cached compound information
                compound_info = compound_info_map[substance]
                istd_name = compound_info['istd']
                istd_row_index = istd_index_map[substance]
                
                # Note: We no longer use pre-calculated NIST ratios from database
                # All NIST calculations now use only actual area values from input file
                
                substance_nist_row = {'Substance': substance}
                substance_agilent_row = {'Substance': substance}
                substance_nist_ratio_row = {'Substance': substance}  # New: for NIST ratios
                
                # ⚡ OPTIMIZED: Process all samples at once using vectorized operations
                istd_found = istd_row_index >= 0
                
                # Get all sample areas at once (vectorized)
                sample_col_indices = [col_to_idx[col] for col in sample_columns if col in col_to_idx]
                raw_substance_areas = area_data.iloc[i, sample_col_indices].values
                
                # ⚡ CRITICAL: Clean and convert all values to numeric (handle strings, NaN, etc.)
                substance_areas = self._clean_area_values(raw_substance_areas)
                
                if istd_found:
                    raw_istd_areas = area_data.iloc[istd_row_index, sample_col_indices].values
                    istd_areas = self._clean_area_values(raw_istd_areas)
                else:
                    istd_areas = np.ones(len(sample_col_indices))  # Avoid division by zero
                
                # Replace zeros with 1 to avoid division by zero
                istd_areas = np.where(istd_areas == 0, 1.0, istd_areas)
                
                # STEP 1: Calculate all ratios at once (vectorized)
                ratios = substance_areas / istd_areas
                
                # Process NIST calculations for each sample
                nist_ratios = np.zeros(len(sample_columns))
                nist_cols_used = []
                
                for idx, sample_col in enumerate(sample_columns):
                    # Get cached NIST column mapping
                    nist_col_used = nist_mapping_cache.get(sample_col, "No NIST columns found")
                    nist_cols_used.append(nist_col_used)
                    
                    if nist_col_used and nist_col_used != "No NIST columns found" and nist_col_used in col_to_idx:
                        try:
                            nist_col_idx = col_to_idx[nist_col_used]
                            raw_nist_substance_area = area_data.iloc[i, nist_col_idx]
                            
                            # ⚡ SAFE: Use data cleaning for individual values
                            clean_nist_substance_area = self._clean_area_values([raw_nist_substance_area])[0]
                            
                            if istd_found:
                                raw_nist_istd_area = area_data.iloc[istd_row_index, nist_col_idx]
                                clean_nist_istd_area = self._clean_area_values([raw_nist_istd_area])[0]
                                
                                if clean_nist_substance_area != 0 and clean_nist_istd_area != 0:
                                    nist_ratios[idx] = clean_nist_substance_area / clean_nist_istd_area
                        except Exception as e:
                            print(f"⚠️ Error getting NIST areas from {nist_col_used}: {e}")
                
                # STEP 2: Calculate NIST results (vectorized)
                final_nist_ratios = np.where(nist_ratios != 0, nist_ratios, 1.0)  # Use 1.0 instead of 0 to avoid division issues
                # ⚡ SAFE: Use numpy's safe division to avoid runtime warnings
                with np.errstate(divide='ignore', invalid='ignore'):
                    nist_results_vec = np.where(final_nist_ratios != 1.0, ratios / final_nist_ratios, 0)
                
                # STEP 3: Calculate Agilent results (vectorized)
                agilent_results_vec = (ratios * 
                                     compound_info['conc_nm'] * 
                                     compound_info['response_factor'] * 
                                     coefficient)
                
                # Store results efficiently
                for idx, sample_col in enumerate(sample_columns):
                    nist_val = float(nist_results_vec[idx])
                    agilent_val = float(agilent_results_vec[idx])
                    
                    # ⚡ DIAGNOSTIC: Check for zero results and log details
                    if substance == 'AcylCarnitine 10:0' and idx < 3:  # Log first 3 samples for debugging
                        ratio_val = float(ratios[idx]) if idx < len(ratios) else 0
                        nist_ratio_val = float(final_nist_ratios[idx]) if idx < len(final_nist_ratios) else 0
                        print(f"🔬 AcylCarnitine 10:0 {sample_col}: ratio={ratio_val:.4f}, nist_ratio={nist_ratio_val:.4f}, NIST={nist_val:.2f}, Agilent={agilent_val:.2f}")
                    
                    substance_nist_row[sample_col] = nist_val
                    substance_agilent_row[sample_col] = agilent_val
                    
                    # Only create detailed calculations on-demand (saves memory and time)
                
                # ⚡ OPTIMIZED: Process NIST columns for ratio calculation (vectorized)
                nist_col_indices = [col_to_idx[col] for col in nist_columns if col in col_to_idx]
                if nist_col_indices:
                    raw_nist_substance_areas = area_data.iloc[i, nist_col_indices].values
                    nist_substance_areas = self._clean_area_values(raw_nist_substance_areas)
                    
                    if istd_found:
                        raw_nist_istd_areas = area_data.iloc[istd_row_index, nist_col_indices].values
                        nist_istd_areas = self._clean_area_values(raw_nist_istd_areas)
                        # Replace zeros with 1 to avoid division by zero
                        nist_istd_areas = np.where(nist_istd_areas == 0, 1.0, nist_istd_areas)
                        nist_ratios_for_substance = nist_substance_areas / nist_istd_areas
                    else:
                        nist_ratios_for_substance = np.zeros(len(nist_col_indices))
                    
                    # Store NIST ratio results
                    for idx, nist_col in enumerate(nist_columns):
                        if idx < len(nist_ratios_for_substance):
                            substance_nist_ratio_row[nist_col] = float(nist_ratios_for_substance[idx])
                
                # Add results to final arrays
                nist_results.append(substance_nist_row)
                agilent_results.append(substance_agilent_row)
                nist_ratio_results.append(substance_nist_ratio_row)
                
                # Generate detailed calculations for more samples (first 25 for better coverage)
                if i < 100:  # Only for first 100 substances to avoid performance impact
                    # ⚡ ENHANCED: Generate details for first 25 samples instead of 10 for better coverage
                    for sample_idx in range(min(25, len(sample_columns))):
                        sample = sample_columns[sample_idx]
                        try:
                            details = self.create_calculation_details_on_demand(
                                area_data, substance, sample, i, istd_index_map, 
                                compound_info_map, nist_mapping_cache, coefficient
                            )
                            detail_key = f"{substance}_{sample}"
                            detailed_calculations[detail_key] = details
                        except Exception as detail_error:
                            # Don't fail the whole calculation for detail errors
                            print(f"⚠️ Failed to create details for {substance}_{sample}: {detail_error}")
            
            print(f"⚡ Performance optimized calculation completed in batches")
            print(f"📊 Generated {len(detailed_calculations)} detailed calculation entries")
            
            # Convert to DataFrames
            nist_df = pd.DataFrame(nist_results)
            agilent_df = pd.DataFrame(agilent_results)
            nist_ratio_df = pd.DataFrame(nist_ratio_results)
            
            # Ensure column order: Substance first, then samples in numerical order
            if len(nist_df.columns) > 1:
                column_order = ['Substance'] + sample_columns
                # Only reorder columns that actually exist in the DataFrame
                existing_columns = [col for col in column_order if col in nist_df.columns]
                nist_df = nist_df[existing_columns]
                agilent_df = agilent_df[existing_columns]
            
            # Ensure column order for NIST ratio results
            if len(nist_ratio_df.columns) > 1:
                nist_column_order = ['Substance'] + nist_columns
                existing_nist_columns = [col for col in nist_column_order if col in nist_ratio_df.columns]
                nist_ratio_df = nist_ratio_df[existing_nist_columns]
            
            print(f"✅ Calculation completed")
            print(f"   NIST results: {nist_df.shape}")
            print(f"   Agilent results: {agilent_df.shape}")
            print(f"   NIST Ratio results: {nist_ratio_df.shape}")
            print(f"   Column order: {list(nist_df.columns)[:10]}...")  # Show first 10 columns
            
            # ⚡ FINAL DIAGNOSTIC: Check AcylCarnitine 10:0 results
            if len(nist_df) > 0:
                acyl_rows = nist_df[nist_df['Substance'] == 'AcylCarnitine 10:0']
                if not acyl_rows.empty:
                    acyl_row = acyl_rows.iloc[0]
                    sample_vals = [f"{col}={acyl_row[col]:.2f}" for col in sample_columns[:3] if col in acyl_row]
                    print(f"✅ AcylCarnitine 10:0 FINAL NIST results: {', '.join(sample_vals)}")
                    
                    if len(agilent_df) > 0:
                        agilent_rows = agilent_df[agilent_df['Substance'] == 'AcylCarnitine 10:0']
                        if not agilent_rows.empty:
                            agilent_row = agilent_rows.iloc[0]
                            agilent_vals = [f"{col}={agilent_row[col]:.2f}" for col in sample_columns[:3] if col in agilent_row]
                            print(f"✅ AcylCarnitine 10:0 FINAL Agilent results: {', '.join(agilent_vals)}")
                else:
                    print(f"❌ AcylCarnitine 10:0 not found in final NIST results!")
                    print(f"   Available substances: {list(nist_df['Substance'].head())}")
            else:
                print(f"❌ No NIST results generated!")
            
            return {
                'nist_data': nist_df,
                'agilent_data': agilent_df,
                'nist_ratio_data': nist_ratio_df,  # New: NIST ratio results
                'detailed_calculations': detailed_calculations,
                'numbering_info': numbering_info,
                'substance_count': len(substances),
                'sample_count': len(sample_columns),
                'nist_column_count': len(nist_columns)
            }
            
        except Exception as e:
            print(f"❌ Calculation error: {e}")
            raise e

    def create_excel_output(self, nist_data, agilent_data, nist_ratio_data=None, filename_base="metabolomics_results"):
        """Create Excel file with 2 or 3 sheets: NIST Results, Agilent Results, and optionally NIST Ratios"""
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write NIST Results sheet
            nist_data.to_excel(writer, sheet_name='NIST Results', index=False)
            
            # Write Agilent Results sheet  
            agilent_data.to_excel(writer, sheet_name='Agilent Results', index=False)
            
            # Write NIST Ratios sheet if provided
            if nist_ratio_data is not None and not nist_ratio_data.empty:
                nist_ratio_data.to_excel(writer, sheet_name='NIST Ratios', index=False)
            
            # Format sheets
            workbook = writer.book
            
            # Format NIST sheet
            nist_sheet = workbook['NIST Results']
            nist_sheet.sheet_properties.tabColor = "0066CC"
            
            # Format Agilent sheet
            agilent_sheet = workbook['Agilent Results']
            agilent_sheet.sheet_properties.tabColor = "FF6600"
            
            # Format NIST Ratios sheet if it exists
            if nist_ratio_data is not None and not nist_ratio_data.empty:
                nist_ratio_sheet = workbook['NIST Ratios']
                nist_ratio_sheet.sheet_properties.tabColor = "00CC66"
        
        output.seek(0)
        return output

    def save_temp_results(self, nist_data, agilent_data, nist_ratio_data=None, detailed_calculations=None):
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
            excel_output = self.create_excel_output(nist_data, agilent_data, nist_ratio_data, filename)
            
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

    def create_calculation_details_on_demand(self, area_data, substance, sample, substance_index, istd_index_map, compound_info_map, nist_mapping_cache, coefficient):
        """Create detailed calculation breakdown on-demand for performance"""
        try:
            compound_info = compound_info_map[substance]
            istd_name = compound_info['istd']
            istd_row_index = istd_index_map[substance]
            istd_found = istd_row_index >= 0
            
            # Get basic area data
            substance_area_raw = area_data.loc[substance_index, sample]
            substance_area = self._clean_area_values([substance_area_raw])[0]
            
            if istd_found:
                istd_area_raw = area_data.loc[istd_row_index, sample]
                istd_area = self._clean_area_values([istd_area_raw])[0]
                if istd_area == 0:
                    istd_area = 1.0  # Avoid division by zero
            else:
                istd_area_raw = 'NOT FOUND'
                istd_area = 1.0
            
            # Calculate ratio
            ratio = substance_area / istd_area
            
            # Get NIST information
            nist_col_used = nist_mapping_cache.get(sample, "No NIST columns found")
            nist_substance_area = 0.0
            nist_istd_area = 0.0
            calculated_nist_ratio = 0.0
            
            if nist_col_used and nist_col_used != "No NIST columns found":
                try:
                    nist_substance_area_raw = area_data.loc[substance_index, nist_col_used]
                    nist_substance_area = self._clean_area_values([nist_substance_area_raw])[0]
                    
                    if istd_found:
                        nist_istd_area_raw = area_data.loc[istd_row_index, nist_col_used]
                        nist_istd_area = self._clean_area_values([nist_istd_area_raw])[0]
                        
                        if nist_istd_area != 0:
                            calculated_nist_ratio = nist_substance_area / nist_istd_area
                except:
                    pass
            
            # Calculate final results
            final_nist_ratio = calculated_nist_ratio if calculated_nist_ratio != 0 else 0
            nist_result = ratio / final_nist_ratio if final_nist_ratio != 0 else 0
            agilent_result = ratio * compound_info['conc_nm'] * compound_info['response_factor'] * coefficient
            
            # Create detailed breakdown
            return {
                'substance': substance,
                'sample': sample,
                'substance_index': substance_index + 1,
                'source_data': {
                    'ph_hc_sample_column': sample,
                    'ph_hc_substance_area_raw': substance_area_raw,
                    'ph_hc_substance_area': substance_area,
                    'ph_hc_istd_area_raw': istd_area_raw,
                    'ph_hc_istd_area': istd_area,
                    'nist_sample_column': nist_col_used,
                    'nist_substance_area_raw': area_data.loc[substance_index, nist_col_used] if nist_col_used != "No NIST columns found" else 'NO NIST COLUMNS',
                    'nist_substance_area': nist_substance_area,
                    'nist_istd_area_raw': area_data.loc[istd_row_index, nist_col_used] if (istd_found and nist_col_used != "No NIST columns found") else 'NOT FOUND',
                    'nist_istd_area': nist_istd_area,
                    'istd_name': istd_name,
                    'istd_found': istd_found,
                    'istd_row_index': istd_row_index + 1 if istd_found else -1,
                    'nist_columns_available': nist_col_used != "No NIST columns found",
                    'nist_matching_logic': f'Matched {sample} → {nist_col_used}' if nist_col_used != "No NIST columns found" else 'No matching possible'
                },
                'database_info': {
                    'istd_name': istd_name,
                    'concentration_nm': compound_info['conc_nm'],
                    'response_factor': compound_info['response_factor'],
                    'coefficient': coefficient,
                    'note': 'NIST calculations use only input file data, no database fallbacks'
                },
                'calculations': {
                    'step_1_ph_hc_ratio': {
                        'formula': 'PH-HC Sample: Substance Area ÷ ISTD Area',
                        'calculation': f"{substance_area} ÷ {istd_area}",
                        'result': ratio,
                        'description': f'Calculate ratio of substance to ISTD in {sample}',
                        'step_name': 'Calculate PH-HC Sample Ratio'
                    },
                    'step_2_nist_ratio': {
                        'formula': 'NIST Sample: Substance Area ÷ ISTD Area (from input file only)',
                        'calculation': f"{nist_substance_area} ÷ {nist_istd_area}" if calculated_nist_ratio != 0 else "NIST data not available in input file",
                        'result': final_nist_ratio,
                        'description': f'Calculate ratio of substance to ISTD in {nist_col_used} (auto-matched)' if calculated_nist_ratio != 0 else 'No NIST data available in input file',
                        'step_name': 'Calculate NIST Sample Ratio'
                    },
                    'step_3_nist_result': {
                        'formula': 'PH-HC Ratio ÷ NIST Ratio (input file data only)',
                        'calculation': f"{ratio} ÷ {final_nist_ratio}" if final_nist_ratio != 0 else f"{ratio} ÷ 0 = Cannot calculate (no NIST data)",
                        'result': nist_result,
                        'description': 'Normalize PH-HC ratio against NIST standard ratio' if final_nist_ratio != 0 else 'Cannot calculate - missing NIST data in input file',
                        'step_name': 'Calculate Normalized NIST Result'
                    },
                    'step_4_agilent': {
                        'formula': 'PH-HC Ratio × Conc.(nM) × Response Factor × Coefficient',
                        'calculation': f"{ratio} × {compound_info['conc_nm']} × {compound_info['response_factor']} × {coefficient}",
                        'result': agilent_result,
                        'description': 'Calculate final concentration using compound database parameters',
                        'step_name': 'Calculate Final Concentration (Agilent)'
                    }
                },
                'final_results': {
                    'ratio': ratio,
                    'nist_result': nist_result,
                    'agilent_result': agilent_result
                }
            }
        except Exception as e:
            return {'error': f'Error creating calculation details: {str(e)}'}

    def get_calculation_details(self, session_id, substance, sample):
        """Get detailed calculation breakdown for a specific substance-sample combination"""
        try:
            temp_dir = tempfile.gettempdir()
            session_dir = os.path.join(temp_dir, f"streamlined_{session_id}")
            details_path = os.path.join(session_dir, f"details_{session_id}.json")
            
            print(f"🔍 Looking for details at: {details_path}")
            
            if not os.path.exists(details_path):
                print(f"❌ Details file not found: {details_path}")
                return {'error': 'Calculation details not found'}
            
            with open(details_path, 'r') as f:
                all_details = json.load(f)
            
            print(f"📊 Found {len(all_details)} total detail entries")
            
            # Try different key formats
            possible_keys = [
                f"{substance}_{sample}",  # Regular PH-HC calculation
                f"{substance}_{sample}_ratio",  # NIST ratio calculation
            ]
            
            # Also try exact match for NIST columns
            for key in all_details.keys():
                if key.startswith(f"{substance}_{sample}"):
                    possible_keys.append(key)
            
            # Find the first matching key
            for calculation_key in possible_keys:
                if calculation_key in all_details:
                    details = all_details[calculation_key]
                    # Add the calculation key for reference
                    details['calculation_key'] = calculation_key
                    return details
            
            # If no match found, return available keys for debugging
            available_keys = [key for key in all_details.keys() if substance in key]
            all_sample_keys = [key for key in all_details.keys() if sample in key]
            
            print(f"❌ No details found for {substance}_{sample}")
            print(f"📊 Available keys for {substance}: {available_keys[:5]}")
            print(f"📊 Available keys for {sample}: {all_sample_keys[:5]}")
            print(f"📊 Tried keys: {possible_keys}")
            
            return {
                'error': f'Details not found for {substance} in {sample}',
                'available_keys_for_substance': available_keys[:10],  # Show first 10 matches
                'available_keys_for_sample': all_sample_keys[:10],
                'tried_keys': possible_keys,
                'total_details': len(all_details)
            }
                
        except Exception as e:
            print(f"❌ Error getting calculation details: {e}")
            return {'error': str(e)}

    def debug_compound_results(self, session_id, compound_name):
        """
        Debug method to analyze why a specific compound might show no results
        """
        try:
            temp_dir = tempfile.gettempdir()
            session_dir = os.path.join(temp_dir, f"streamlined_{session_id}")
            
            # Check if session data exists
            excel_files = [f for f in os.listdir(session_dir) if f.endswith('.xlsx')]
            json_files = [f for f in os.listdir(session_dir) if f.endswith('.json')]
            
            debug_info = {
                'compound': compound_name,
                'session_files': {
                    'excel': excel_files,
                    'json': json_files
                },
                'compound_info': self.get_compound_info(compound_name),
                'normalized_variations': self._normalize_compound_name(compound_name)[:5]  # First 5 variations
            }
            
            # Check if compound exists in normalized mapping
            debug_info['in_database'] = compound_name in self._compound_name_map
            
            # Look for similar compounds
            debug_info['similar_compounds'] = [
                key for key in self._compound_name_map.keys() 
                if compound_name.replace(' ', '').lower() in key.replace(' ', '').lower()
            ][:10]
            
            return debug_info
            
        except Exception as e:
            return {'error': f'Debug error: {str(e)}'}

# Global instance
streamlined_calculator = StreamlinedCalculatorService()