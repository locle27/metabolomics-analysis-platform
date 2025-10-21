#!/usr/bin/env python3
"""
STREAMLINED METABOLOMICS CALCULATION SERVICE
Complete recreation based on user specifications
Single input file → 3-step calculation → 2-sheet output + preview

NOW WITH INTELLIGENT FILE FORMAT DETECTION:
- Auto-detects any file structure
- Handles multi-row headers
- Supports any sample pattern (PH-HC_, SL_, Alz_, custom)
- Handles interleaved NIST columns
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
from file_format_detector import FileFormatDetector
from calculation_handlers import CalculationHandlerFactory

class StreamlinedCalculatorService:
    """Professional metabolomics calculator with 3-step formula + intelligent format detection"""

    def __init__(self):
        self.ratio_database = self._load_ratio_database()
        self.sample_index = self._load_sample_index()
        self.compound_index = self._load_compound_index()
        self.format_detector = FileFormatDetector()  # NEW: Intelligent format detection

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

                    print(f"   Columns: {list(df.columns)}")
                    return df

            print("⚠️ Ratio-database.xlsx not found in any location, using fallback")
            return None
        except Exception as e:
            print(f"⚠️ Error loading Ratio database: {e}")
            return None

    def _load_sample_index(self):
        """Load sample index mapping from database with Excel fallback"""
        try:
            # Try loading from database first (supports multiple patterns)
            from models import SampleIndex
            samples = SampleIndex.query.all()
            if samples:
                data = {
                    'sample': [s.sample for s in samples],
                    'paired_nist': [s.paired_nist for s in samples]
                }
                df = pd.DataFrame(data)
                print(f"✅ Loaded {len(df)} sample index entries from database")
                return df
        except Exception as e:
            print(f"⚠️ Could not load from database: {e}, trying Excel files")

        # Fallback to Excel file
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
                    print(f"✅ Loaded {len(df)} sample index entries from Excel")
                    return df

            print("⚠️ sample-index.xlsx not found in any location, using dynamic mapping")
            return None
        except Exception as e:
            print(f"⚠️ Error loading Sample index: {e}")
            return None

    def _load_compound_index(self):
        """
        Load compound index with ISTD mappings - DATABASE FIRST PRIORITY

        Order of priority:
        1. PostgreSQL database (891 compounds) - PREFERRED
        2. Excel file fallback (807 compounds) - OUTDATED, only for offline use
        """
        try:
            # 🔥 PRIORITY 1: Try database first (complete data)
            try:
                compounds = CompoundIndex.query.all()
                data = []
                for comp in compounds:
                    data.append({
                        'Compound': comp.compound,
                        'ISTD': comp.istd,
                        'Conc. (nM)': comp.conc_nm,
                        'Response factor': comp.response_factor
                    })
                df = pd.DataFrame(data) if data else None
                if df is not None and len(df) > 0:
                    print(f"✅ Loaded {len(df)} compounds from PostgreSQL database")
                    return df
            except Exception as db_error:
                print(f"⚠️ Database not accessible: {db_error}")
                print("   Falling back to Excel file (may be outdated)")

            # 🔶 FALLBACK: Try Excel file (outdated, missing 84 compounds)
            possible_paths = [
                "/mnt/c/Users/T14/Desktop/metabolomics-project/compound-index.xlsx",
                "/mnt/c/Users/T14/Desktop/compound-index.xlsx",
                "compound-index.xlsx",
                "./compound-index.xlsx"
            ]

            for compound_file in possible_paths:
                if os.path.exists(compound_file):
                    df = pd.read_excel(compound_file)
                    print(f"⚠️ WARNING: Using outdated Excel file ({len(df)} compounds)")
                    print(f"   Database has 891 compounds, Excel has {len(df)} - missing {891 - len(df)} compounds")
                    return df

            print("❌ ERROR: No compound source available (neither database nor Excel)")
            return None

        except Exception as e:
            print(f"❌ Error loading Compound index: {e}")
            return None

    def _normalize_compound_name(self, compound_name):
        """
        Ultra-comprehensive lipid name normalization for complex chemical notation:
            pass  # Fixed empty block
        - Handles fatty acid notation (16:0, 20:4, etc.)
        - Complex nested structures like 22:5(n3)/20:1
        - Mixed bracket types: [], (), {}
        - Lipid class prefixes: (O-), (P-), etc.
        - Position indicators: [a], [b], [sn1], [sn2]
        - Multiple separators: /, -, space
        - Lipid class abbreviations: AcylCarnitine ↔ AC, etc.
        """
        if not compound_name or pd.isna(compound_name):
            return [""]

        import re
        name = str(compound_name).strip()
        variations = [name]

        # === STEP 0: Handle lipid class abbreviation expansions/contractions ===
        # CRITICAL: Excel files use full names, database uses abbreviations
        lipid_class_mappings = [
            ('AcylCarnitine ', 'AC('),  # "AcylCarnitine 10:0" → "AC(10:0)"
            ('AcylCarnitine(', 'AC('),  # "AcylCarnitine(10:0)" → "AC(10:0)"
            ('Acyl Carnitine ', 'AC('), # "Acyl Carnitine 10:0" → "AC(10:0)"
            ('AC(', 'AcylCarnitine '),  # Reverse: "AC(10:0)" → "AcylCarnitine 10:0"
            ('AC ', 'AcylCarnitine '),  # "AC 10:0" → "AcylCarnitine 10:0"
        ]

        abbreviation_variations = []
        for variant in variations[:]:
            for full_form, abbrev_form in lipid_class_mappings:
                # Try replacing full form with abbreviation
                if full_form in variant:
                    new_variant = variant.replace(full_form, abbrev_form)
                    # If we added opening parenthesis, we need closing too
                    if abbrev_form.endswith('(') and ')' not in new_variant:
                        # Find the end of the fatty acid notation (before space or end)
                        match = re.search(r'AC\(([^\s)]+)', new_variant)
                        if match:
                            fatty_acid = match.group(1)
                            new_variant = new_variant.replace(f'AC({fatty_acid}', f'AC({fatty_acid})')
                    abbreviation_variations.append(new_variant)

                # Try replacing abbreviation with full form
                if abbrev_form in variant:
                    # Need to be careful with parentheses
                    if abbrev_form.endswith('('):
                        # Extract fatty acid from AC(10:0) format
                        match = re.search(r'AC\(([^)]+)\)', variant)
                        if match:
                            fatty_acid = match.group(1)
                            new_variant = variant.replace(f'AC({fatty_acid})', f'{full_form.rstrip("(")}{fatty_acid}')
                            abbreviation_variations.append(new_variant)
                    else:
                        new_variant = variant.replace(abbrev_form, full_form)
                        abbreviation_variations.append(new_variant)

        variations.extend(abbreviation_variations)

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
            pass  # Fixed empty block
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

    def refresh_from_database(self):
        """
        🔄 Refresh compound index from PostgreSQL database
        Call this method when you have app context to ensure latest data
        """
        try:
            compounds = CompoundIndex.query.all()
            data = []
            for comp in compounds:
                data.append({
                    'Compound': comp.compound,
                    'ISTD': comp.istd,
                    'Conc. (nM)': comp.conc_nm,
                    'Response factor': comp.response_factor
                })
            df = pd.DataFrame(data) if data else None
            if df is not None and len(df) > 0:
                self.compound_index = df
                # Rebuild the compound name map with fresh data
                self._compound_name_map = self._create_compound_name_map()
                print(f"✅ Refreshed {len(df)} compounds from PostgreSQL database")
                return True
        except Exception as e:
            print(f"⚠️ Could not refresh from database: {e}")
            return False

    def _create_compound_name_map(self):
        """Create a mapping of normalized compound names to original database entries"""
        compound_map = {}

        if self.compound_index is None:
            return compound_map



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


        return compound_map

    def determine_sample_numbering(self, sample_columns):
        """
        Determine sample numbering and pattern based on input file:
        - PH-HC_1-100 → NIST_1-100(1), NIST_1-100(2), etc. (25 samples per NIST)
        - SL_1-50 → NIST_SL (1) (50 samples per NIST)
        - Auto-detects pattern from column names
        """

        # Check if sample index database is available
        if self.sample_index is not None and len(self.sample_index) > 0:
            print(f"✅ Using sample index from database ({len(self.sample_index)} entries)")
            # Database will handle mapping directly in find_matching_nist_column
            return {
                'base_number': 1,
                'sample_range': 'database',
                'nist_patterns': [],
                'use_database': True
            }

        # Extract sample numbers from PH-HC_XXXX or SL_XXXX format
        sample_numbers = []
        sample_pattern = None

        for col in sample_columns:
            try:
                col_str = str(col)
                # Detect Second List pattern (SL_)
                if 'SL_' in col_str:
                    num_str = col_str.replace('SL_', '')
                    if num_str.isdigit():
                        sample_numbers.append(int(num_str))
                        sample_pattern = 'SL'
                # Detect original PH-HC_ pattern
                elif 'PH-HC_' in col_str:
                    num_str = col_str.replace('PH-HC_', '')
                    if num_str.isdigit():
                        sample_numbers.append(int(num_str))
                        sample_pattern = 'PH-HC'
            except:
                continue

        if not sample_numbers:
            print("⚠️ No valid PH-HC_ or SL_ samples found, using default numbering")
            return {
                'base_number': 1,
                'sample_range': '1-100',
                'nist_patterns': ['NIST_1-100 (1)', 'NIST_1-100 (2)', 'NIST_1-100 (3)', 'NIST_1-100 (4)'],
                'use_database': False
            }

        # Handle Second List pattern (50 samples per 1 NIST)
        if sample_pattern == 'SL':
            print(f"✅ Detected Second List pattern: SL_1 to SL_{max(sample_numbers)}")
            return {
                'base_number': 1,
                'sample_range': f'1-{max(sample_numbers)}',
                'nist_patterns': ['NIST_SL (1)'],
                'pattern_type': 'SL',
                'use_database': False
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


        print(f"   Base range: {sample_range}")
        print(f"   NIST patterns: {nist_patterns}")

        return {
            'base_number': base_hundred,
            'sample_range': sample_range,
            'nist_patterns': nist_patterns,
            'actual_range': f"{min_sample}-{max_sample}",
            'use_database': False
        }

    def find_matching_nist_column(self, ph_hc_sample, nist_columns):
        """
        Find the correct NIST column that matches a sample.
        Supports multiple patterns:
        - Database lookup (PH-HC_ or SL_ samples)
        - PH-HC_6 → NIST_1-100 (1) [if 6 is in range 1-100]
        - SL_25 → NIST_SL (1) [Second List pattern]
        """
        if not nist_columns:
            return None

        # Try database lookup first
        if self.sample_index is not None and len(self.sample_index) > 0:
            try:
                sample_name = str(ph_hc_sample)
                match = self.sample_index[self.sample_index['sample'] == sample_name]
                if not match.empty:
                    paired_nist = match.iloc[0]['paired_nist']
                    # Find matching NIST column
                    for nist_col in nist_columns:
                        if paired_nist in str(nist_col):
                            return nist_col
            except Exception as e:
                print(f"⚠️ Database lookup failed: {e}, falling back to pattern matching")

        # Extract sample number from PH-HC_ or SL_ column
        try:
            sample_str = str(ph_hc_sample)
            sample_num = None

            # Check for SL_ pattern
            if 'SL_' in sample_str:
                sample_num_str = sample_str.replace('SL_', '')
                if sample_num_str.isdigit():
                    sample_num = int(sample_num_str)
                    # Second List: all samples use NIST_SL (1)
                    for nist_col in nist_columns:
                        if 'NIST_SL (1)' in str(nist_col) or 'NIST_SL(1)' in str(nist_col):
                            return nist_col
                    return None

            # Check for PH-HC_ pattern
            elif 'PH-HC_' in sample_str:
                sample_num_str = sample_str.replace('PH-HC_', '')
                if sample_num_str.isdigit():
                    sample_num = int(sample_num_str)
            else:
                return None

            if sample_num is None:
                return None

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

            return


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
            pass  # Range analysis complete



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
        """
        Get compound information (ISTD, concentration, response factor)

        PRIORITY ORDER:
        1. Fresh PostgreSQL database query (ALWAYS has latest ISTD updates)
        2. Cached DataFrame (fallback only if database unavailable)
        """

        # 🔥 PRIORITY: Try fresh database query FIRST (always has latest ISTDs)
        try:
            compound = CompoundIndex.query.filter_by(compound=substance).first()
            if compound:
                return {
                    'istd': compound.istd,
                    'conc_nm': float(compound.conc_nm),
                    'response_factor': float(compound.response_factor)
                }
        except Exception as db_error:
            # Database not available or compound not found - fall through to DataFrame
            pass

        # Fallback to DataFrame if database query fails
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

                    return compound_info

                # Try all variations of the input substance name
                substance_variations = self._normalize_compound_name(substance)
                for variant in substance_variations:
                    if variant in self._compound_name_map:
                        compound_info = self._compound_name_map[variant]

                        return compound_info

            # If still no match, return None to indicate missing compound
            # Caller should handle missing compounds appropriately
            variations_tried = self._normalize_compound_name(substance)
            print(f"❌ MISSING: Compound '{substance}' not found in database after trying {len(variations_tried)} variations")
            return None  # Return None instead of fallback

        except Exception as e:
            print(f"⚠️ Error getting compound info for {substance}: {e}")
            return None  # Return None instead of fallback

    def debug_excel_structure(self, area_file):
        """Debug function to analyze Excel file structure"""
        try:
            area_data = pd.read_excel(area_file)

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

            return {'error': str(e)}

    def calculate_streamlined(self, area_file, coefficient=500):
        """
        Main calculation function with 3-step formula:
            pass  # Fixed empty block
        1. Ratio = Substance Area ÷ ISTD Area
        2. NIST = Substance Ratio ÷ NIST Standard Ratio
        3. Agilent = Ratio × Conc.(nM) × Response Factor × Coefficient
        """

        print(f"   Coefficient: {coefficient}")

        try:
            # 🔥 REFRESH FROM DATABASE: Ensure we have latest compound data (891 compounds)
            print("\n🔄 Refreshing compound data from PostgreSQL database...")
            refresh_success = self.refresh_from_database()
            if not refresh_success:
                print("⚠️ Using cached compound data (may be from outdated Excel file)")

            # ⚡ INTELLIGENT FILE FORMAT DETECTION
            print("\n🧠 Using intelligent file format detector...")

            # Detect file format automatically
            format_info = self.format_detector.analyze_file(area_file)

            # Prepare clean dataframe with proper structure
            area_data = self.format_detector.prepare_dataframe(area_file)

            # Get sample-to-NIST mapping from detector
            sample_to_nist_map = self.format_detector.get_sample_to_nist_mapping()

            print(f"\n✅ File loaded with intelligent detection:")
            print(f"   Pattern: {format_info['sample_pattern']}")
            print(f"   Samples: {format_info['num_samples']}")
            print(f"   NIST standards: {len(format_info['nist_columns'])}")

            # Use the detected compound column
            compound_column = 'Compound'  # Already standardized by detector

            # Check if compound column has valid data
            if compound_column not in area_data.columns:
                raise ValueError(f"Selected compound column '{compound_column}' not found in file")

            # Use the detected compound column
            raw_substances = area_data[compound_column].dropna().tolist()

            # ⚡ ULTRA ENHANCED: Robust compound filtering with detailed validation
            header_keywords = ['Name', 'Compound', 'Substance', 'Chemical', 'Area', 'Sample', 'Method', 'Compound Method', 'nan']
            substances = []
            filtered_items = []



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



            # Use detected columns from intelligent format detector
            sample_columns = format_info['sample_columns']
            nist_columns = format_info['nist_columns']

            print(f"\n✅ Detected columns:")
            print(f"   Sample columns: {len(sample_columns)} ({sample_columns[0] if sample_columns else 'none'} ... {sample_columns[-1] if sample_columns else 'none'})")
            print(f"   NIST columns: {nist_columns}")

            # Columns are already sorted by detector in their natural file order






            # ⚡ DIAGNOSTIC: Verify data extraction for first compound
            if len(substances) > 0:
                first_compound = substances[0]
                first_index = 0

                print(f"\n🔍 First compound verification: {first_compound}")

                # Check the raw compound name in that row
                actual_compound_name = area_data.iloc[first_index][compound_column]
                print(f"   Actual compound name in DataFrame: '{actual_compound_name}'")

                # Deep dive into area values with enhanced diagnostic
                for idx, col in enumerate(sample_columns[:3]):
                    if col in area_data.columns:
                        raw_area_val = area_data.iloc[first_index][col]
                        cleaned_area_val = self._clean_area_values([raw_area_val])[0]
                        print(f"   {col}: raw={raw_area_val}, cleaned={cleaned_area_val}")

                        # Enhanced diagnostic info
                        val_type = type(raw_area_val).__name__
                        is_numeric = isinstance(raw_area_val, (int, float, np.number))
                        print(f"      {col}: raw='{raw_area_val}' (type={val_type}, numeric={is_numeric}) → cleaned={cleaned_area_val}")

                        # Critical check for string contamination
                        if isinstance(raw_area_val, str) and raw_area_val.strip().upper() == 'AREA':

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

                print(f"      Available LPC d7 compounds: {istd_candidates[:5]}")

                if 'LPC 18:1 d7' in substances:
                    istd_index = substances.index('LPC 18:1 d7')


                    # Deep ISTD diagnostic
                    for idx, col in enumerate(sample_columns[:3]):
                        if col in area_data.columns:
                            istd_raw = area_data.iloc[istd_index][col]
                            istd_cleaned = self._clean_area_values([istd_raw])[0]
                            istd_type = type(istd_raw).__name__
                            print(f"      {col}: ISTD raw='{istd_raw}' (type={istd_type}) → cleaned={istd_cleaned}")
                else:

                    if istd_candidates:
                        closest_istd = istd_candidates[0]
                        print(f"      Using closest match: '{closest_istd}'")

            else:

                # Enhanced compound searching
                acyl_patterns = ['AcylCarnitine', 'Acyl', 'Carnitine', '10:0']


                for pattern in acyl_patterns:
                    matches = [s for s in substances if pattern in s][:5]
                    if matches:
                        print(f"      Pattern '{pattern}': {matches}")
                    else:
                        print(f"      Pattern '{pattern}': No matches")

                # Show first 20 substances for reference


            print(f"")  # Blank line for readability
            self.analyze_nist_column_ranges(nist_columns)

            # Determine sample numbering
            numbering_info = self.determine_sample_numbering(sample_columns)

            # 🚀 PERFORMANCE OPTIMIZATION: Pre-compute mappings to avoid O(n²) complexity


            # Pre-compute ISTD index mappings to avoid nested loops
            istd_index_map = {}
            compound_info_map = {}
            missing_compounds = []  # Track compounds not found in database

            for i, substance in enumerate(substances):
                compound_info = self.get_compound_info(substance)

                # Check if compound was found in database
                if compound_info is None:
                    missing_compounds.append(substance)
                    # Use minimal defaults to allow processing to continue
                    compound_info = {
                        'istd': 'MISSING',
                        'conc_nm': 0.0,
                        'response_factor': 0.0
                    }

                compound_info_map[substance] = compound_info
                istd_name = compound_info['istd']

                # Find ISTD index once for this substance
                for j, comp_name in enumerate(substances):
                    if istd_name in str(comp_name):
                        istd_index_map[substance] = j
                        break
                else:
                    istd_index_map[substance] = -1  # ISTD not found

            # Use intelligent detector's sample-to-NIST mapping (already computed)
            nist_mapping_cache = sample_to_nist_map
            print(f"\n✅ Using intelligent sample-to-NIST mapping ({len(nist_mapping_cache)} mappings)")



            # Convert DataFrame to numpy for faster access
            area_values = area_data.select_dtypes(include=[np.number]).values
            numeric_columns = area_data.select_dtypes(include=[np.number]).columns.tolist()

            # Create column index mappings for fast lookup
            col_to_idx = {col: idx for idx, col in enumerate(area_data.columns)}

            # 🚀 NEW: Use specialized calculation handler based on format type
            print(f"\n{'='*80}")
            print(f"🎯 SELECTING CALCULATION HANDLER")
            print(f"{'='*80}")

            # Get appropriate handler for this format
            handler = CalculationHandlerFactory.get_handler(format_info, self)

            # Delegate calculation to specialized handler
            calculation_results = handler.calculate(
                area_data=area_data,
                format_info=format_info,
                sample_to_nist_map=sample_to_nist_map,
                compound_info_map=compound_info_map,
                istd_index_map=istd_index_map,
                substances=substances,
                coefficient=coefficient
            )

            # Extract results from handler
            nist_df = calculation_results['nist_data']
            agilent_df = calculation_results['agilent_data']
            nist_ratio_df = calculation_results['nist_ratio_data']

            # 📝 OLD CALCULATION LOOP REPLACED BY HANDLER SYSTEM
            # The old inline calculation has been moved to calculation_handlers.py
            # for better separation of concerns and format-specific optimizations

            detailed_calculations = {}  # Detailed calculations moved to handlers

            # ⚡ The entire calculation loop (160+ lines) has been replaced with handler.calculate()
            # Old code removed for clarity - see calculation_handlers.py for implementation

            # DataFrames already created by handler (nist_df, agilent_df, nist_ratio_df)

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


                    if len(agilent_df) > 0:
                        agilent_rows = agilent_df[agilent_df['Substance'] == 'AcylCarnitine 10:0']
                        if not agilent_rows.empty:
                            agilent_row = agilent_rows.iloc[0]
                            agilent_vals = [f"{col}={agilent_row[col]:.2f}" for col in sample_columns[:3] if col in agilent_row]

                else:

                    print(f"   Available substances: {list(nist_df['Substance'].head())}")
            else:


                pass  # Fixed empty block

            # ⚠️ REPORT MISSING COMPOUNDS
            if missing_compounds:
                print("\n" + "="*80)
                print("❌ ERROR: COMPOUNDS NOT FOUND IN DATABASE")
                print("="*80)
                print(f"\n{len(missing_compounds)} compounds were not found in the database:")
                print("\nMissing compounds list:")
                for idx, compound in enumerate(missing_compounds[:100], 1):  # Show first 100
                    print(f"  {idx}. {compound}")
                if len(missing_compounds) > 100:
                    print(f"\n  ... and {len(missing_compounds) - 100} more")

                print(f"\n⚠️ These compounds have been processed with placeholder values:")
                print(f"   - ISTD: MISSING")
                print(f"   - Concentration: 0.0 nM")
                print(f"   - Response Factor: 0.0")
                print(f"\n💡 ACTION REQUIRED:")
                print(f"   Add these {len(missing_compounds)} compounds to the database with correct ISTD mappings")
                print(f"   before processing this file for production use.")
                print("="*80 + "\n")

                # Optionally raise an exception to stop processing
                # Uncomment the line below if you want to abort on missing compounds
                # raise ValueError(f"{len(missing_compounds)} compounds missing from database")
            else:
                print("\n✅ All compounds found in database - no missing entries")

            return {
                'nist_data': nist_df,
                'agilent_data': agilent_df,
                'nist_ratio_data': nist_ratio_df,  # New: NIST ratio results
                'detailed_calculations': detailed_calculations,
                'numbering_info': numbering_info,
                'substance_count': len(substances),
                'sample_count': len(sample_columns),
                'nist_column_count': len(nist_columns),
                'missing_compounds': missing_compounds,  # Include missing compounds in results
                # 🔥 NEW: Session data for on-demand calculation details
                'area_data': area_data,
                'substances': substances,
                'coefficient': coefficient,
                'format_info': format_info,
                'sample_to_nist_map': sample_to_nist_map,
                'compound_info_map': compound_info_map,
                'istd_index_map': istd_index_map
            }

        except Exception as e:

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

    def save_temp_results(self, nist_data, agilent_data, nist_ratio_data=None, detailed_calculations=None,
                          area_data=None, substances=None, coefficient=500, format_info=None,
                          sample_to_nist_map=None, compound_info_map=None, istd_index_map=None):
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

            # Save detailed calculations as JSON (legacy - usually empty now)
            if detailed_calculations:
                details_path = os.path.join(session_dir, f"details_{session_id}.json")
                with open(details_path, 'w') as f:
                    # Convert numpy types to native Python types for JSON serialization
                    json_safe_details = {}
                    for key, value in detailed_calculations.items():
                        json_safe_details[key] = self._make_json_safe(value)

                    json.dump(json_safe_details, f, indent=2)

            # 🔥 NEW: Save session data for on-demand calculation details
            if area_data is not None and substances is not None:
                print(f"💾 Saving session data for on-demand calculation details...")

                # Save area data as Excel
                area_path = os.path.join(session_dir, f"area_{session_id}.xlsx")
                area_data.to_excel(area_path)
                print(f"✅ Saved area data: {area_path}")

                # Save metadata as JSON
                meta_path = os.path.join(session_dir, f"meta_{session_id}.json")
                metadata = {
                    'substances': substances if substances else [],
                    'coefficient': coefficient,
                    'format_info': format_info if format_info else {},
                    'sample_to_nist_map': sample_to_nist_map if sample_to_nist_map else {},
                    'compound_info_map': self._make_json_safe(compound_info_map) if compound_info_map else {},
                    'istd_index_map': self._make_json_safe(istd_index_map) if istd_index_map else {},
                    'session_id': session_id,
                    'timestamp': timestamp
                }

                with open(meta_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                print(f"✅ Saved metadata: {meta_path}")
                print(f"📊 Metadata includes: {len(substances)} substances, {len(compound_info_map)} compound mappings")

            return {
                'session_id': session_id,
                'filename': filename,
                'temp_path': excel_path,
                'session_dir': session_dir
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
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
            # 🔥 FIX: Get FRESH compound info from database instead of stale metadata
            fresh_compound_info = self.get_compound_info(substance)
            if fresh_compound_info:
                # Use fresh database data (includes updated ISTDs)
                compound_info = fresh_compound_info
                istd_name = fresh_compound_info['istd']

                # 🔥 CRITICAL: Recalculate ISTD row index based on fresh ISTD name
                # The metadata istd_index_map is stale and points to old ISTD rows
                # Get compound names from 'Compound' column, not from index (which is just 0,1,2,...)
                if 'Compound' in area_data.columns:
                    substances_list = area_data['Compound'].tolist()
                else:
                    substances_list = list(area_data.index)  # Fallback

                istd_row_index = -1
                for idx, comp_name in enumerate(substances_list):
                    if istd_name in str(comp_name):
                        istd_row_index = idx
                        break
                istd_found = istd_row_index >= 0
            else:
                # Fallback to metadata if database lookup fails
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

    def create_nist_calculation_details_on_demand(self, area_data, substance, nist_col, substance_index, istd_index_map, compound_info_map, coefficient):
        """Create detailed NIST calculation breakdown on-demand for NIST columns"""
        try:
            # 🔥 FIX: Get FRESH compound info from database instead of stale metadata
            fresh_compound_info = self.get_compound_info(substance)
            if fresh_compound_info:
                # Use fresh database data (includes updated ISTDs)
                compound_info = fresh_compound_info
                istd_name = fresh_compound_info['istd']

                # 🔥 CRITICAL: Recalculate ISTD row index based on fresh ISTD name
                # The metadata istd_index_map is stale and points to old ISTD rows
                # Get compound names from 'Compound' column, not from index (which is just 0,1,2,...)
                if 'Compound' in area_data.columns:
                    substances_list = area_data['Compound'].tolist()
                else:
                    substances_list = list(area_data.index)  # Fallback

                istd_row_index = -1
                for idx, comp_name in enumerate(substances_list):
                    if istd_name in str(comp_name):
                        istd_row_index = idx
                        break
                istd_found = istd_row_index >= 0
            else:
                # Fallback to metadata if database lookup fails
                compound_info = compound_info_map[substance]
                istd_name = compound_info['istd']
                istd_row_index = istd_index_map[substance]
                istd_found = istd_row_index >= 0

            # Get NIST column area data
            nist_substance_area_raw = area_data.loc[substance_index, nist_col]
            nist_substance_area = self._clean_area_values([nist_substance_area_raw])[0]

            if istd_found:
                nist_istd_area_raw = area_data.loc[istd_row_index, nist_col]
                nist_istd_area = self._clean_area_values([nist_istd_area_raw])[0]
                if nist_istd_area == 0:
                    nist_istd_area = 1.0  # Avoid division by zero
            else:
                nist_istd_area_raw = 'NOT FOUND'
                nist_istd_area = 1.0

            # Calculate NIST ratio
            nist_ratio = nist_substance_area / nist_istd_area

            # Create detailed breakdown for NIST ratio calculation
            return {
                'substance': substance,
                'sample': nist_col,
                'substance_index': substance_index + 1,
                'calculation_type': 'NIST_RATIO',
                'source_data': {
                    'nist_sample_column': nist_col,
                    'nist_substance_area_raw': nist_substance_area_raw,
                    'nist_substance_area': nist_substance_area,
                    'nist_istd_area_raw': nist_istd_area_raw,
                    'nist_istd_area': nist_istd_area,
                    'istd_name': istd_name,
                    'istd_found': istd_found,
                    'istd_row_index': istd_row_index + 1 if istd_found else -1,
                },
                'database_info': {
                    'istd_name': istd_name,
                    'concentration_nm': compound_info['conc_nm'],
                    'response_factor': compound_info['response_factor'],
                    'coefficient': coefficient,
                    'note': 'NIST ratio calculation uses only input file data'
                },
                'calculations': {
                    'nist_ratio_calculation': {
                        'formula': 'NIST Ratio = Substance Area ÷ ISTD Area',
                        'calculation': f"{nist_substance_area} ÷ {nist_istd_area}",
                        'result': nist_ratio,
                        'description': f'Calculate ratio of {substance} to {istd_name} in {nist_col}',
                        'step_name': 'Calculate NIST Standard Ratio'
                    }
                },
                'final_results': {
                    'nist_ratio': nist_ratio,
                    'note': 'This ratio is used as the NIST standard for normalizing PH-HC calculations'
                }
            }
        except Exception as e:
            return {'error': f'Error creating NIST calculation details: {str(e)}'}

    def get_calculation_details(self, session_id, substance, sample):
        """Get detailed calculation breakdown for a specific substance-sample combination"""
        try:
            temp_dir = tempfile.gettempdir()
            session_dir = os.path.join(temp_dir, f"streamlined_{session_id}")
            details_path = os.path.join(session_dir, f"details_{session_id}.json")

            # 🔥 NEW: If details file doesn't exist, check if we have session data for on-demand creation
            if not os.path.exists(details_path):
                print(f"⚠️ Details file not found: {details_path}")
                print(f"🔄 Attempting on-demand calculation detail generation...")

                # Check if session directory and Excel files exist
                if not os.path.exists(session_dir):
                    return {'error': f'Session directory not found: {session_dir}'}

                # Try to load area data and metadata for on-demand creation
                try:
                    area_path = os.path.join(session_dir, f"area_{session_id}.xlsx")
                    meta_path = os.path.join(session_dir, f"meta_{session_id}.json")

                    if not os.path.exists(area_path) or not os.path.exists(meta_path):
                        return {
                            'error': 'Session data not found for on-demand calculation',
                            'debug': {
                                'session_dir': session_dir,
                                'area_file_exists': os.path.exists(area_path),
                                'meta_file_exists': os.path.exists(meta_path)
                            }
                        }

                    # Load metadata
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)

                    # Load area data
                    area_data = pd.read_excel(area_path, index_col=0)

                    # Get required parameters from metadata
                    substances = metadata.get('substances', [])
                    coefficient = metadata.get('coefficient', 500)
                    format_info = metadata.get('format_info', {})
                    sample_to_nist_map = metadata.get('sample_to_nist_map', {})
                    compound_info_map = metadata.get('compound_info_map', {})
                    istd_index_map = metadata.get('istd_index_map', {})

                    # Find substance index
                    if substance not in substances:
                        return {
                            'error': f'Substance "{substance}" not found in session data',
                            'available_substances': substances[:20]
                        }

                    substance_index = substances.index(substance)

                    # Create calculation details on-demand
                    details = self.create_calculation_details_on_demand(
                        area_data=area_data,
                        substance=substance,
                        sample=sample,
                        substance_index=substance_index,
                        istd_index_map=istd_index_map,
                        compound_info_map=compound_info_map,
                        nist_mapping_cache=sample_to_nist_map,
                        coefficient=coefficient
                    )

                    print(f"✅ On-demand calculation details created successfully")
                    return details

                except Exception as on_demand_error:
                    print(f"❌ On-demand creation failed: {on_demand_error}")
                    import traceback
                    traceback.print_exc()
                    return {
                        'error': f'Failed to create calculation details on-demand: {str(on_demand_error)}'
                    }

            with open(details_path, 'r') as f:
                all_details = json.load(f)




            # Create comprehensive list of possible key formats to try
            possible_keys = []

            # Standard formats
            possible_keys.append(f"{substance}_{sample}")  # Regular PH-HC calculation
            possible_keys.append(f"{substance}_{sample}_ratio")  # NIST ratio calculation

            # URL encoding variations (in case of encoding issues)
            import urllib.parse
            encoded_sample = urllib.parse.quote(sample)
            decoded_sample = urllib.parse.unquote(sample)
            possible_keys.append(f"{substance}_{encoded_sample}")
            possible_keys.append(f"{substance}_{decoded_sample}")

            # Handle NIST column variations with parentheses and spaces
            if 'NIST' in sample:
                # Try variations with and without spaces around parentheses
                variations = [
                    sample,  # Original
                    sample.replace(' (', '_('),  # Space before paren to underscore
                    sample.replace('(', ' ('),  # Ensure space before paren
                    sample.replace(' ', '_'),  # All spaces to underscores
                    sample.replace('(', '').replace(')', ''),  # Remove parentheses
                ]

                for variation in variations:
                    possible_keys.append(f"{substance}_{variation}")
                    possible_keys.append(f"{substance}_{variation}_ratio")

            # Fuzzy matching - find keys that contain both substance and sample parts
            sample_parts = sample.replace('(', '').replace(')', '').replace('_', ' ').split()
            for key in all_details.keys():
                if substance in key:
                    # Check if key contains major parts of the sample name
                    key_matches_sample = False
                    if 'NIST' in sample and 'NIST' in key:
                        # For NIST columns, check if the range matches
                        if any(part in key for part in sample_parts if part.replace('-', '').isdigit() or '-' in part):
                            key_matches_sample = True
                    elif sample in key or any(part in key for part in sample_parts if len(part) > 3):
                        key_matches_sample = True

                    if key_matches_sample and key not in possible_keys:
                        possible_keys.append(key)

            # Remove duplicates while preserving order
            seen = set()
            possible_keys = [key for key in possible_keys if not (key in seen or seen.add(key))]



            # Find the first matching key
            for calculation_key in possible_keys:
                if calculation_key in all_details:
                    details = all_details[calculation_key]
                    # Add the calculation key for reference
                    details['calculation_key'] = calculation_key

                    return details

            # If no match found, return available keys for debugging
            available_keys = [key for key in all_details.keys() if substance in key]
            all_sample_keys = [key for key in all_details.keys() if any(part in key for part in sample.split() if len(part) > 2)]






            return {
                'error': f'Details not found for {substance} in {sample}',
                'available_keys_for_substance': available_keys[:10],  # Show first 10 matches
                'available_keys_for_sample': all_sample_keys[:10],
                'tried_keys': possible_keys[:15],  # Show first 15 tried keys
                'total_details': len(all_details),
                'debug_info': {
                    'substance_param': substance,
                    'sample_param': sample,
                    'sample_parts': sample.split(),
                    'all_keys_sample': list(all_details.keys())
                }
            }

        except Exception as e:

            import traceback
            traceback.print_exc()
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
