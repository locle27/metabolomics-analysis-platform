#!/usr/bin/env python3
"""
INTELLIGENT FILE FORMAT DETECTOR
Automatically detects and adapts to any metabolomics file structure
Handles: multi-row headers, any sample patterns, interleaved NIST columns
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional

class FileFormatDetector:
    """
    Smart file format detection for metabolomics data files
    Adapts to any file structure automatically
    """

    def __init__(self):
        self.detected_format = {}

    def analyze_file(self, file_path_or_df) -> Dict:
        """
        Comprehensive file analysis - returns complete format specification

        Returns:
            {
                'header_row': int,           # Which row contains actual data headers
                'data_start_row': int,       # First row of actual compound data
                'compound_columns': List[str],   # Columns containing compound names
                'sample_columns': List[str],     # Sample data columns (ordered)
                'nist_columns': List[str],       # NIST standard columns (ordered)
                'sample_pattern': str,           # Detected pattern (PH-HC, SL, Alz, etc.)
                'sample_to_nist_map': Dict,      # Sample -> NIST mapping
                'num_samples': int,              # Total sample count
                'samples_per_nist': Dict,        # NIST -> sample count mapping
            }
        """
        # Load file
        if isinstance(file_path_or_df, str):
            df_raw = pd.read_excel(file_path_or_df, header=None)
        else:
            df_raw = file_path_or_df.copy()

        print("\n" + "="*80)
        print("🔍 INTELLIGENT FILE FORMAT DETECTION")
        print("="*80)

        # Step 1: Find header row
        header_row = self._detect_header_row(df_raw)
        print(f"\n✅ Header row detected: Row {header_row}")

        # Step 2: Find data start row
        data_start_row = self._detect_data_start_row(df_raw, header_row)
        print(f"✅ Data starts at: Row {data_start_row}")

        # Step 3: Extract and classify columns
        columns = self._extract_columns(df_raw, header_row)
        column_classification = self._classify_columns(columns)

        print(f"\n📊 Column Classification:")
        print(f"   Compound columns: {len(column_classification['compound'])}")
        print(f"   Sample columns: {len(column_classification['sample'])}")
        print(f"   NIST columns: {len(column_classification['nist'])}")
        print(f"   Metadata columns: {len(column_classification['metadata'])}")

        # Step 4: Detect sample pattern
        sample_pattern = self._detect_sample_pattern(column_classification['sample'])
        print(f"\n🎯 Sample Pattern: {sample_pattern}")

        # Step 5: Map samples to NIST (handle interleaved columns)
        sample_to_nist_map = self._map_samples_to_nist(
            column_classification['sample'],
            column_classification['nist'],
            columns  # Full column list with order
        )

        # Step 6: Calculate statistics
        samples_per_nist = self._calculate_samples_per_nist(sample_to_nist_map)

        print(f"\n📈 Sample Distribution:")
        for nist, count in samples_per_nist.items():
            print(f"   {nist}: {count} samples")

        # Store results
        self.detected_format = {
            'header_row': header_row,
            'data_start_row': data_start_row,
            'compound_columns': column_classification['compound'],
            'sample_columns': column_classification['sample'],
            'nist_columns': column_classification['nist'],
            'metadata_columns': column_classification['metadata'],
            'sample_pattern': sample_pattern,
            'sample_to_nist_map': sample_to_nist_map,
            'num_samples': len(column_classification['sample']),
            'samples_per_nist': samples_per_nist,
            'all_columns_ordered': columns
        }

        print("\n" + "="*80)
        print("✅ FORMAT DETECTION COMPLETE")
        print("="*80)

        return self.detected_format

    def _detect_header_row(self, df: pd.DataFrame) -> int:
        """
        Find the row that contains actual column headers (sample names, NIST labels)
        Skip metadata rows like "Area", "Transition", etc.
        """
        for row_idx in range(min(10, len(df))):
            row = df.iloc[row_idx]

            # Check if this row contains sample/NIST column names
            row_str = ' '.join(str(x) for x in row if pd.notna(x))

            # Look for sample patterns
            has_samples = bool(re.search(r'(PH-HC_|SL_|Alz_|\w+_)\d+', row_str))
            has_nist = bool(re.search(r'NIST', row_str, re.IGNORECASE))
            has_compound = bool(re.search(r'(Compound|Name|Substance)', row_str, re.IGNORECASE))

            if (has_samples or has_nist) and has_compound:
                return row_idx

        return 0  # Default to first row

    def _detect_data_start_row(self, df: pd.DataFrame, header_row: int) -> int:
        """
        Find the first row that contains actual numeric data (not metadata)
        """
        for row_idx in range(header_row + 1, min(header_row + 10, len(df))):
            row = df.iloc[row_idx]

            # Skip rows that are all text (like "Area", "Transition")
            numeric_count = sum(1 for x in row if isinstance(x, (int, float)) and pd.notna(x))

            # If row has significant numeric data, it's the data start
            if numeric_count > len(row) * 0.3:  # At least 30% numeric
                return row_idx

        return header_row + 1  # Default to next row after header

    def _extract_columns(self, df: pd.DataFrame, header_row: int) -> List[str]:
        """Extract column names from detected header row"""
        columns = []
        for col in df.iloc[header_row]:
            if pd.notna(col):
                columns.append(str(col).strip())
            else:
                columns.append('Unnamed')
        return columns

    def _classify_columns(self, columns: List[str]) -> Dict[str, List[str]]:
        """
        Classify each column into categories:
        - compound: Compound name columns
        - sample: Sample data columns (PH-HC_, SL_, Alz_, etc.)
        - nist: NIST standard columns
        - metadata: Extra info (Transition, Method, etc.)
        - ignore: Unnamed, empty, etc.
        """
        classification = {
            'compound': [],
            'sample': [],
            'nist': [],
            'metadata': [],
            'ignore': []
        }

        for col in columns:
            col_lower = col.lower()

            # NIST columns (highest priority)
            if 'nist' in col_lower:
                classification['nist'].append(col)

            # Sample columns (any prefix with number)
            elif re.search(r'(PH-HC_|SL_|Alz_|Sample_|S_|HC_)\d+', col, re.IGNORECASE):
                classification['sample'].append(col)

            # Generic numbered samples (S1, Sample1, etc.)
            elif re.search(r'(Sample|S|HC)\d+', col, re.IGNORECASE):
                classification['sample'].append(col)

            # Compound columns
            elif re.search(r'(Compound|Name|Substance|Method)', col, re.IGNORECASE):
                classification['compound'].append(col)

            # Metadata
            elif re.search(r'(Transition|Area|Method|ID|Index)', col, re.IGNORECASE):
                classification['metadata'].append(col)

            # Unnamed/ignore
            elif 'unnamed' in col_lower or col.strip() == '':
                classification['ignore'].append(col)

            # Unknown - assume metadata
            else:
                classification['metadata'].append(col)

        return classification

    def _detect_sample_pattern(self, sample_columns: List[str]) -> str:
        """
        Detect the naming pattern used for samples
        Returns the common prefix (PH-HC, SL, Alz, etc.)
        """
        if not sample_columns:
            return "Unknown"

        # Extract prefixes from all sample columns
        prefixes = set()
        for col in sample_columns:
            match = re.match(r'([A-Za-z_-]+)_?(\d+)', col)
            if match:
                prefixes.add(match.group(1))

        # Return most common prefix
        if len(prefixes) == 1:
            return list(prefixes)[0]
        elif len(prefixes) > 1:
            return f"Mixed ({', '.join(sorted(prefixes))})"
        else:
            return "Unknown"

    def _map_samples_to_nist(self, sample_cols: List[str], nist_cols: List[str],
                            all_columns: List[str]) -> Dict[str, str]:
        """
        Map each sample to its corresponding NIST column
        Handles interleaved NIST columns (NIST in middle of samples)

        Strategy:
        1. Find position of each sample and NIST in full column list
        2. Assign each sample to the nearest preceding or following NIST
        3. Handle edge cases (NIST before first sample, after last sample)
        """
        if not nist_cols:
            return {sample: "No NIST" for sample in sample_cols}

        # Build position map
        col_positions = {col: idx for idx, col in enumerate(all_columns)}

        sample_to_nist = {}

        # For each sample, find the appropriate NIST column
        for sample in sample_cols:
            sample_pos = col_positions.get(sample, -1)

            # Find nearest NIST (prefer the one AFTER the sample group)
            nearest_nist = None
            min_distance = float('inf')

            for nist in nist_cols:
                nist_pos = col_positions.get(nist, -1)

                # Strategy: Use the NIST that comes AFTER this sample
                # But if no NIST after, use the one before
                if nist_pos > sample_pos:  # NIST after sample
                    distance = nist_pos - sample_pos
                    if distance < min_distance:
                        min_distance = distance
                        nearest_nist = nist

            # If no NIST found after, use the last NIST before
            if nearest_nist is None:
                for nist in reversed(nist_cols):
                    nist_pos = col_positions.get(nist, -1)
                    if nist_pos < sample_pos:
                        nearest_nist = nist
                        break

            # Last resort: use first NIST
            if nearest_nist is None:
                nearest_nist = nist_cols[0]

            sample_to_nist[sample] = nearest_nist

        return sample_to_nist

    def _calculate_samples_per_nist(self, sample_to_nist_map: Dict[str, str]) -> Dict[str, int]:
        """Calculate how many samples use each NIST standard"""
        samples_per_nist = {}
        for sample, nist in sample_to_nist_map.items():
            samples_per_nist[nist] = samples_per_nist.get(nist, 0) + 1
        return samples_per_nist

    def prepare_dataframe(self, file_path_or_df) -> pd.DataFrame:
        """
        Load and prepare dataframe with proper headers and structure
        Returns clean dataframe ready for calculation
        """
        # Analyze format if not done yet
        if not self.detected_format:
            self.analyze_file(file_path_or_df)

        # Load file
        if isinstance(file_path_or_df, str):
            df = pd.read_excel(
                file_path_or_df,
                header=self.detected_format['header_row'],
                skiprows=range(0, self.detected_format['header_row'])
            )
        else:
            df = file_path_or_df.copy()

        # Skip metadata rows between header and data
        rows_to_skip = self.detected_format['data_start_row'] - self.detected_format['header_row'] - 1
        if rows_to_skip > 0:
            df = df.iloc[rows_to_skip:].reset_index(drop=True)

        # Find actual compound columns in loaded dataframe (handle 'Unnamed' variations)
        actual_compound_cols = []
        transition_cols = []  # Separate transition/method columns

        for stored_col in self.detected_format['compound_columns']:
            if stored_col in df.columns:
                # Check if this looks like a transition column by sampling data
                if self._column_looks_like_transition(df, stored_col):
                    transition_cols.append(stored_col)
                else:
                    actual_compound_cols.append(stored_col)
            elif 'Unnamed' in stored_col:
                # Find any 'Unnamed:*' column in the dataframe
                for df_col in df.columns:
                    if 'Unnamed' in str(df_col) and df_col not in actual_compound_cols and df_col not in transition_cols:
                        # Check if it's a transition column
                        if self._column_looks_like_transition(df, df_col):
                            transition_cols.append(df_col)
                        else:
                            actual_compound_cols.append(df_col)
                        break

        # Use only compound columns (don't merge with transition data)
        if len(actual_compound_cols) > 1:
            # Multiple compound columns - merge them (rare case)
            df['Compound'] = df[actual_compound_cols].apply(
                lambda row: ' | '.join(str(x) for x in row if pd.notna(x)),
                axis=1
            )
            df = df.drop(columns=actual_compound_cols)
        elif len(actual_compound_cols) == 1:
            # Single compound column - just rename (most common)
            df = df.rename(columns={actual_compound_cols[0]: 'Compound'})
        else:
            # No compound columns found - use first column
            first_col = df.columns[0]
            df = df.rename(columns={first_col: 'Compound'})

        # Keep transition data separate (don't merge with compound names)
        if transition_cols:
            df['_transition'] = df[transition_cols[0]]
            print(f"   ✅ Transition/Method column kept separate (not merged with compound names)")

        # CRITICAL: Strip all whitespace from compound names for exact database matching
        if 'Compound' in df.columns:
            df['Compound'] = df['Compound'].str.strip()
            print(f"   ✅ Compound names cleaned (stripped whitespace)")

        print("\n✅ Dataframe prepared and ready for calculation")
        print(f"   Shape: {df.shape}")
        print(f"   Compounds: {len(df)}")
        print(f"   Sample columns: {len(self.detected_format['sample_columns'])}")

        return df

    def _column_looks_like_transition(self, df: pd.DataFrame, col_name: str) -> bool:
        """
        Check if a column contains transition/method data (e.g., "316.3 -> 85.1")
        Returns True if column looks like transition data
        """
        if col_name not in df.columns:
            return False

        # Sample first few non-null values
        sample_values = df[col_name].dropna().head(10).astype(str).tolist()

        if not sample_values:
            return False

        # Check if values match transition patterns
        transition_indicators = 0
        for val in sample_values:
            val_str = str(val).strip()
            # Common transition patterns: "316.3 -> 85.1", "922.8 -> 922.8", etc.
            if '->' in val_str or '→' in val_str:
                transition_indicators += 1
            # Check for numeric.numeric pattern (mass spec transitions)
            elif re.match(r'^\d+\.?\d*\s*->\s*\d+\.?\d*$', val_str):
                transition_indicators += 1

        # If more than 50% of samples look like transitions, it's a transition column
        return transition_indicators > len(sample_values) * 0.5

    def get_sample_to_nist_mapping(self) -> Dict[str, str]:
        """Get the detected sample-to-NIST mapping"""
        return self.detected_format.get('sample_to_nist_map', {})

    def export_pattern_to_database(self, db, SampleIndex):
        """
        Export detected pattern to database for future reuse
        """
        try:
            pattern_name = self.detected_format['sample_pattern']
            sample_to_nist = self.detected_format['sample_to_nist_map']

            added_count = 0
            for sample, nist in sample_to_nist.items():
                # Check if exists
                existing = SampleIndex.query.filter_by(sample=sample).first()
                if not existing:
                    entry = SampleIndex(
                        sample=sample,
                        paired_nist=nist
                    )
                    db.session.add(entry)
                    added_count += 1

            db.session.commit()
            print(f"\n✅ Exported {added_count} new sample mappings to database")
            return True

        except Exception as e:
            print(f"\n⚠️ Could not export to database: {e}")
            db.session.rollback()
            return False


# Utility function for easy use
def analyze_file_format(file_path):
    """Quick analysis of any file format"""
    detector = FileFormatDetector()
    format_info = detector.analyze_file(file_path)
    return detector, format_info
