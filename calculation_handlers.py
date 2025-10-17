"""
CALCULATION HANDLERS FOR DIFFERENT FILE FORMATS
================================================

This module provides specialized calculation handlers for different metabolomics file formats.
Each handler implements the same 3-step calculation formula but with format-specific optimizations.

Format 1 (PH-HC): Original system with 100 samples, 4 NIST standards
Format 2 (ALZ/SL): New system with variable samples, variable NIST standards
"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod


class BaseCalculationHandler(ABC):
    """
    Abstract base class for calculation handlers.
    Defines the common interface and shared logic.
    """

    def __init__(self, calculator_service):
        """
        Initialize handler with reference to main calculator service

        Args:
            calculator_service: StreamlinedCalculatorService instance (for shared resources)
        """
        self.calculator = calculator_service

    @abstractmethod
    def get_format_name(self):
        """Return the format name for logging"""
        pass

    @abstractmethod
    def validate_format(self, format_info):
        """
        Validate that the detected format matches this handler

        Args:
            format_info: Dictionary from FileFormatDetector.analyze_file()

        Returns:
            bool: True if this handler can process the format
        """
        pass

    def calculate(self, area_data, format_info, sample_to_nist_map,
                  compound_info_map, istd_index_map, substances, coefficient):
        """
        Main calculation method - implements 3-step formula:
        1. Ratio = Substance Area ÷ ISTD Area
        2. NIST = Ratio ÷ NIST Ratio (from file)
        3. Agilent = Ratio × Conc.(nM) × Response Factor × Coefficient

        Args:
            area_data: Cleaned DataFrame with compound areas
            format_info: Format detection results
            sample_to_nist_map: Sample -> NIST column mapping
            compound_info_map: Compound -> info dictionary mapping
            istd_index_map: Compound -> ISTD row index mapping
            substances: List of compound names
            coefficient: Multiplier for Agilent calculation

        Returns:
            dict: Results with nist_data, agilent_data, nist_ratio_data DataFrames
        """
        print(f"\n{'='*80}")
        print(f"🧮 {self.get_format_name()} CALCULATION")
        print(f"{'='*80}")

        sample_columns = format_info['sample_columns']
        nist_columns = format_info['nist_columns']

        print(f"Samples: {len(sample_columns)}")
        print(f"NIST Standards: {len(nist_columns)}")
        print(f"Substances: {len(substances)}")
        print(f"Coefficient: {coefficient}")

        # Convert DataFrame to numpy for faster access
        col_to_idx = {col: idx for idx, col in enumerate(area_data.columns)}

        # Initialize results
        nist_results = []
        agilent_results = []
        nist_ratio_results = []

        # Process each substance
        for i, substance in enumerate(substances):
            if i % 100 == 0 and i > 0:
                print(f"  Processed {i}/{len(substances)} substances...")

            # Get cached compound information
            compound_info = compound_info_map[substance]
            istd_row_index = istd_index_map[substance]

            substance_nist_row = {'Substance': substance}
            substance_agilent_row = {'Substance': substance}
            substance_nist_ratio_row = {'Substance': substance}

            # ⚡ OPTIMIZED: Process all samples at once using vectorized operations
            istd_found = istd_row_index >= 0

            # Get all sample areas at once (vectorized)
            sample_col_indices = [col_to_idx[col] for col in sample_columns if col in col_to_idx]
            raw_substance_areas = area_data.iloc[i, sample_col_indices].values

            # Clean and convert all values to numeric
            substance_areas = self.calculator._clean_area_values(raw_substance_areas)

            if istd_found:
                raw_istd_areas = area_data.iloc[istd_row_index, sample_col_indices].values
                istd_areas = self.calculator._clean_area_values(raw_istd_areas)
            else:
                istd_areas = np.ones(len(sample_col_indices))  # Avoid division by zero

            # Replace zeros with 1 to avoid division by zero
            istd_areas = np.where(istd_areas == 0, 1.0, istd_areas)

            # STEP 1: Calculate all ratios at once (vectorized)
            ratios = substance_areas / istd_areas

            # Process NIST calculations for each sample
            nist_ratios = np.zeros(len(sample_columns))

            for idx, sample_col in enumerate(sample_columns):
                # Get NIST column mapping
                nist_col_used = sample_to_nist_map.get(sample_col, None)

                if nist_col_used and nist_col_used in col_to_idx:
                    try:
                        nist_col_idx = col_to_idx[nist_col_used]
                        raw_nist_substance_area = area_data.iloc[i, nist_col_idx]

                        clean_nist_substance_area = self.calculator._clean_area_values([raw_nist_substance_area])[0]

                        if istd_found:
                            raw_nist_istd_area = area_data.iloc[istd_row_index, nist_col_idx]
                            clean_nist_istd_area = self.calculator._clean_area_values([raw_nist_istd_area])[0]

                            if clean_nist_substance_area != 0 and clean_nist_istd_area != 0:
                                nist_ratios[idx] = clean_nist_substance_area / clean_nist_istd_area
                    except Exception as e:
                        print(f"⚠️ Error getting NIST areas from {nist_col_used}: {e}")

            # STEP 2: Calculate NIST results (vectorized)
            final_nist_ratios = np.where(nist_ratios != 0, nist_ratios, 1.0)
            with np.errstate(divide='ignore', invalid='ignore'):
                nist_results_vec = np.where(final_nist_ratios != 1.0, ratios / final_nist_ratios, 0)

            # STEP 3: Calculate Agilent results (vectorized)
            agilent_results_vec = (ratios *
                                 compound_info['conc_nm'] *
                                 compound_info['response_factor'] *
                                 coefficient)

            # Store results
            for idx, sample_col in enumerate(sample_columns):
                substance_nist_row[sample_col] = float(nist_results_vec[idx])
                substance_agilent_row[sample_col] = float(agilent_results_vec[idx])

            # Process NIST ratio columns
            nist_col_indices = [col_to_idx[col] for col in nist_columns if col in col_to_idx]
            if nist_col_indices:
                raw_nist_substance_areas = area_data.iloc[i, nist_col_indices].values
                nist_substance_areas = self.calculator._clean_area_values(raw_nist_substance_areas)

                if istd_found:
                    raw_nist_istd_areas = area_data.iloc[istd_row_index, nist_col_indices].values
                    nist_istd_areas = self.calculator._clean_area_values(raw_nist_istd_areas)
                    nist_istd_areas = np.where(nist_istd_areas == 0, 1.0, nist_istd_areas)
                    nist_ratios_for_substance = nist_substance_areas / nist_istd_areas
                else:
                    nist_ratios_for_substance = np.zeros(len(nist_col_indices))

                for idx, nist_col in enumerate(nist_columns):
                    if idx < len(nist_ratios_for_substance):
                        substance_nist_ratio_row[nist_col] = float(nist_ratios_for_substance[idx])

            # Add results to final arrays
            nist_results.append(substance_nist_row)
            agilent_results.append(substance_agilent_row)
            nist_ratio_results.append(substance_nist_ratio_row)

        # Convert to DataFrames
        nist_df = pd.DataFrame(nist_results)
        agilent_df = pd.DataFrame(agilent_results)
        nist_ratio_df = pd.DataFrame(nist_ratio_results)

        print(f"\n✅ {self.get_format_name()} calculation complete!")
        print(f"   NIST results: {nist_df.shape}")
        print(f"   Agilent results: {agilent_df.shape}")
        print(f"   NIST Ratio results: {nist_ratio_df.shape}")

        return {
            'nist_data': nist_df,
            'agilent_data': agilent_df,
            'nist_ratio_data': nist_ratio_df
        }


class PHHC_CalculationHandler(BaseCalculationHandler):
    """
    Handler for Format 1: PH-HC Pattern

    Characteristics:
    - Fixed structure: 100 samples per file
    - 4 NIST standards (25 samples per NIST)
    - Pattern: PH-HC_X where X is sequential
    - NIST columns at end of file
    - Fixed naming: NIST_X-Y (1), (2), (3), (4)
    """

    def get_format_name(self):
        return "FORMAT 1: PH-HC (100 samples, 4 NIST)"

    def validate_format(self, format_info):
        """Validate PH-HC format"""
        pattern = format_info.get('sample_pattern', '')
        num_samples = format_info.get('num_samples', 0)
        num_nist = len(format_info.get('nist_columns', []))

        # PH-HC format has:
        # - Sample pattern starts with 'PH-HC'
        # - Typically 100 samples (can be flexible for partial files)
        # - 4 NIST standards
        is_phhc = pattern.startswith('PH-HC')
        has_expected_nist = num_nist == 4

        return is_phhc and has_expected_nist

    def calculate(self, area_data, format_info, sample_to_nist_map,
                  compound_info_map, istd_index_map, substances, coefficient):
        """
        PH-HC specific calculation

        Uses standard 3-step formula with optimizations for fixed structure:
        - Fixed 25 samples per NIST standard
        - Predictable NIST mapping
        - Can leverage batch processing more efficiently
        """
        print(f"\n📊 PH-HC Format Specifics:")
        print(f"   - Expected samples: ~100 (actual: {len(format_info['sample_columns'])})")
        print(f"   - Expected NIST: 4 (actual: {len(format_info['nist_columns'])})")
        print(f"   - Samples per NIST: ~25")

        # Use base calculation method
        return super().calculate(area_data, format_info, sample_to_nist_map,
                                compound_info_map, istd_index_map, substances, coefficient)


class ALZSL_CalculationHandler(BaseCalculationHandler):
    """
    Handler for Format 2: ALZ/SL Pattern

    Characteristics:
    - Variable samples per file (40 in ALZ, 50 in SL, custom possible)
    - Variable NIST standards (2 in ALZ, 1 in SL, custom possible)
    - Pattern: Alz_X or SL_X or custom prefix
    - NIST columns interleaved in file (can be anywhere)
    - Position-based sample-to-NIST mapping
    - Multi-row headers with metadata
    """

    def get_format_name(self):
        return "FORMAT 2: ALZ/SL (Variable samples/NIST)"

    def validate_format(self, format_info):
        """Validate ALZ/SL format"""
        pattern = format_info.get('sample_pattern', '')

        # ALZ/SL format has:
        # - Sample pattern is NOT PH-HC (anything else is considered Format 2)
        # - Can have any number of samples and NIST standards
        # - Flexible structure
        is_alzsl = not pattern.startswith('PH-HC')

        return is_alzsl

    def calculate(self, area_data, format_info, sample_to_nist_map,
                  compound_info_map, istd_index_map, substances, coefficient):
        """
        ALZ/SL specific calculation

        Uses standard 3-step formula with optimizations for flexible structure:
        - Variable samples per NIST
        - Position-based NIST mapping (already computed by detector)
        - Handles interleaved NIST columns
        """
        print(f"\n📊 ALZ/SL Format Specifics:")
        print(f"   - Detected pattern: {format_info['sample_pattern']}")
        print(f"   - Samples: {len(format_info['sample_columns'])}")
        print(f"   - NIST standards: {len(format_info['nist_columns'])}")
        print(f"   - NIST distribution:")

        # Show sample distribution per NIST
        nist_distribution = {}
        for sample, nist in sample_to_nist_map.items():
            nist_distribution[nist] = nist_distribution.get(nist, 0) + 1

        for nist_col, count in nist_distribution.items():
            print(f"     {nist_col}: {count} samples")

        # Use base calculation method
        return super().calculate(area_data, format_info, sample_to_nist_map,
                                compound_info_map, istd_index_map, substances, coefficient)


class CalculationHandlerFactory:
    """
    Factory class to select the appropriate calculation handler based on format detection
    """

    @staticmethod
    def get_handler(format_info, calculator_service):
        """
        Select and return the appropriate calculation handler

        Args:
            format_info: Dictionary from FileFormatDetector.analyze_file()
            calculator_service: StreamlinedCalculatorService instance

        Returns:
            BaseCalculationHandler: Appropriate handler for the detected format
        """
        # Try PH-HC handler first
        phhc_handler = PHHC_CalculationHandler(calculator_service)
        if phhc_handler.validate_format(format_info):
            print(f"\n✅ Selected: {phhc_handler.get_format_name()}")
            return phhc_handler

        # Default to ALZ/SL handler (flexible for any non-PH-HC format)
        alzsl_handler = ALZSL_CalculationHandler(calculator_service)
        print(f"\n✅ Selected: {alzsl_handler.get_format_name()}")
        return alzsl_handler
