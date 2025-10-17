# Calculation Handlers Architecture

## Overview

The metabolomics calculation system has been split into **two specialized handlers** to ensure accurate calculations for different file format types.

## System Architecture

```
StreamlinedCalculatorService
    |
    |-- FileFormatDetector (detects format)
    |
    |-- CalculationHandlerFactory (selects appropriate handler)
            |
            |-- PHHC_CalculationHandler (Format 1)
            |
            |-- ALZSL_CalculationHandler (Format 2)
```

## Format Types

### Format 1: PH-HC (Original System)

**Characteristics:**
- Fixed structure: **100 samples** per file
- **4 NIST standards** (25 samples per NIST)
- Sample pattern: `PH-HC_XXXX` (sequential numbers)
- NIST naming: `NIST_X-Y (1)`, `(2)`, `(3)`, `(4)`
- NIST columns at **end** of file
- **Predictable NIST mapping** (fixed 25 samples per standard)

**Example File:**
```
Compound | PH-HC_5701 | PH-HC_5702 | ... | PH-HC_5800 | NIST_5701-5800 (1) | NIST_5701-5800 (2) | NIST_5701-5800 (3) | NIST_5701-5800 (4)
```

**Handler:** `PHHC_CalculationHandler`

### Format 2: ALZ/SL (New System)

**Characteristics:**
- **Variable samples** per file (40 in ALZ, 50 in SL, custom possible)
- **Variable NIST** standards (2 in ALZ, 1 in SL, custom possible)
- Sample patterns: `Alz_X`, `SL_X`, or custom prefix
- NIST naming: `NIST_NAME (N)` - varies by file
- NIST columns **interleaved** in file (can be anywhere)
- **Position-based sample-to-NIST mapping**
- Multi-row headers with metadata

**Example File (ALZ):**
```
Compound Method | Alz_1 | ... | Alz_24 | NIST_ALZ (1) | Alz_25 | ... | Alz_40 | NIST_ALZ (2)
Name | Transition | Area | ... | Area | Area | Area | ... | Area | Area
```

**Handler:** `ALZSL_CalculationHandler`

## Calculation Formula

**Both formats use the SAME 3-step calculation formula:**

1. **Ratio** = Substance Area ÷ ISTD Area
2. **NIST** = Ratio ÷ NIST Ratio (from input file)
3. **Agilent** = Ratio × Conc.(nM) × Response Factor × Coefficient

The difference is NOT in the formula but in:
- File structure handling
- Sample-to-NIST mapping logic
- Header processing
- Column detection

## How It Works

### 1. Format Detection

```python
# Automatic format detection
format_info = file_format_detector.analyze_file(input_file)

# Returns:
{
    'sample_pattern': 'PH-HC_' or 'Alz_' or 'SL_' or custom,
    'num_samples': 100 or 40 or 50 or custom,
    'nist_columns': ['NIST_X (1)', 'NIST_X (2)', ...],
    'sample_to_nist_map': {sample: nist_column, ...}
}
```

### 2. Handler Selection

```python
# Factory selects appropriate handler
handler = CalculationHandlerFactory.get_handler(format_info, calculator_service)

# Selection logic:
if sample_pattern.startswith('PH-HC') and num_nist == 4:
    return PHHC_CalculationHandler()  # Format 1
else:
    return ALZSL_CalculationHandler()  # Format 2 (flexible)
```

### 3. Calculation

```python
# Delegate to specialized handler
results = handler.calculate(
    area_data=cleaned_dataframe,
    format_info=format_detection_results,
    sample_to_nist_map=sample_nist_mapping,
    compound_info_map=compound_database_info,
    istd_index_map=istd_row_indices,
    substances=list_of_compounds,
    coefficient=500
)

# Returns:
{
    'nist_data': DataFrame,      # NIST results
    'agilent_data': DataFrame,   # Agilent results
    'nist_ratio_data': DataFrame # NIST ratios
}
```

## Key Benefits

### 1. Separation of Concerns
- Format detection isolated in `FileFormatDetector`
- Calculation logic isolated in handlers
- Main calculator orchestrates the flow

### 2. Maintainability
- Each format has its own handler class
- Easy to add new formats (create new handler)
- Clear structure for debugging

### 3. Accuracy
- Format-specific optimizations
- No cross-contamination between formats
- Explicit validation per format type

### 4. Flexibility
- Format 2 handler can handle ANY pattern (not just ALZ/SL)
- Easy to extend for future formats
- Backward compatible with existing code

## Test Results

### Format 1: PH-HC
```
✅ FORMAT 1 SUCCESS
   Pattern: PH-HC_
   Samples: 100
   NIST: 4
   Substances: 406
   Missing compounds: 0
```

### Format 2: ALZ
```
✅ FORMAT 2 SUCCESS
   Pattern: Alz_
   Samples: 40
   NIST: 2
   Substances: 523
   Missing compounds: 0
```

## Code Structure

### Files

- **`calculation_handlers.py`** - Handler classes and factory
  - `BaseCalculationHandler` - Abstract base class with shared logic
  - `PHHC_CalculationHandler` - Format 1 handler
  - `ALZSL_CalculationHandler` - Format 2 handler
  - `CalculationHandlerFactory` - Handler selection

- **`streamlined_calculator_service.py`** - Main orchestrator
  - Uses `CalculationHandlerFactory` to select handler
  - Delegates calculation to selected handler
  - Handles pre/post processing

- **`file_format_detector.py`** - Format detection
  - Auto-detects file structure
  - Provides format info to factory

### Class Hierarchy

```
BaseCalculationHandler (ABC)
    |
    |-- get_format_name() [abstract]
    |-- validate_format() [abstract]
    |-- calculate() [implemented - shared logic]
    |
    |-- PHHC_CalculationHandler
    |       |-- Validates PH-HC format
    |       |-- Optimized for fixed structure
    |
    |-- ALZSL_CalculationHandler
            |-- Validates non-PH-HC formats
            |-- Flexible for variable structures
```

## Future Enhancements

### Adding a New Format

1. Create new handler class inheriting from `BaseCalculationHandler`
2. Implement `get_format_name()` and `validate_format()`
3. Optionally override `calculate()` for custom logic
4. Update `CalculationHandlerFactory.get_handler()` to include new handler

Example:
```python
class CustomFormatHandler(BaseCalculationHandler):
    def get_format_name(self):
        return "FORMAT 3: Custom Pattern"

    def validate_format(self, format_info):
        # Custom validation logic
        return format_info['sample_pattern'] == 'CUSTOM_'

    # Use inherited calculate() or override as needed
```

## Conclusion

The two-handler architecture provides:
- ✅ Clear separation between format types
- ✅ Accurate calculations for both formats
- ✅ Easy maintenance and debugging
- ✅ Future-proof extensibility
- ✅ Same calculation formula, different file handling
