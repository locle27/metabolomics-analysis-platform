# Second List Lipidomic Pattern Setup

## Overview

The Streamlined Calculator now supports **multiple sample index patterns** for different lipidomic analysis projects:

1. **Original Pattern (PH-HC_)**: 100 samples with 4 NIST standards (25 samples per NIST)
2. **Second List Pattern (SL_)**: 50 samples with 1 NIST standard (50 samples per NIST)

## Database Structure

### Sample Index Table
The `sample_index` table stores sample-to-NIST mappings for all patterns:

| sample | paired_nist |
|--------|-------------|
| PH-HC_1 | NIST_1-100 (1) |
| PH-HC_2 | NIST_1-100 (1) |
| ... | ... |
| SL_1 | NIST_SL (1) |
| SL_2 | NIST_SL (1) |
| ... | ... |
| SL_50 | NIST_SL (1) |

### Compound Index Table
The `compound_index` table stores compound-to-ISTD mappings:

| compound | istd | conc_nm |
|----------|------|---------|
| AcylCarnitine 10:0 | LPC 18:1 d7 | 0.0 |
| LPC 17:1 | LPC 18:1 d7 | 0.0 |
| ... | ... | ... |

Currently contains **891 compounds** (525 from Second List + 366 from original).

## Migration Script

### Running the Migration

```bash
python3 migrate_second_list_sample_index.py
```

The script will:
1. ✅ Create 50 sample index entries (SL_1 to SL_50)
2. ✅ Pair each sample with NIST_SL (1)
3. ✅ Import 525 compound mappings from Second List Lipidomic.xlsx
4. ✅ Skip duplicates if compounds already exist
5. ✅ Verify migration success

### Migration Results

```
✅ Successfully inserted 50 sample index entries
✅ Successfully added 74 new compounds
⚠️  Skipped 451 duplicate compounds
✅ Total compounds in database: 891
```

## How the Calculator Works

### 1. Pattern Detection

The calculator **automatically detects** which pattern to use based on input file column names:

**Input File Columns:**
- `SL_1`, `SL_2`, ..., `SL_50` → **Second List Pattern**
- `PH-HC_1`, `PH-HC_2`, ..., `PH-HC_100` → **Original Pattern**

### 2. Sample Index Lookup

**Priority order:**
1. **Database lookup** (supports all patterns)
2. **Excel fallback** (sample-index.xlsx)
3. **Dynamic pattern matching** (last resort)

### 3. NIST Mapping

**Second List Pattern (SL_):**
- All 50 samples → `NIST_SL (1)`
- Simple 1:1 mapping

**Original Pattern (PH-HC_):**
- Samples 1-25 → `NIST_1-100 (1)`
- Samples 26-50 → `NIST_1-100 (2)`
- Samples 51-75 → `NIST_1-100 (3)`
- Samples 76-100 → `NIST_1-100 (4)`

## Input File Requirements

### Second List Lipidomic Input Format

Your Excel file should have these columns:

| Compound | SL_1 | SL_2 | ... | SL_50 | NIST_SL (1) |
|----------|------|------|-----|-------|-------------|
| AcylCarnitine 10:0 | 123.45 | 234.56 | ... | 345.67 | 456.78 |
| LPC 17:1 | 789.01 | 890.12 | ... | 901.23 | 012.34 |

**Required:**
- ✅ `Compound` column (compound names)
- ✅ `SL_1` to `SL_50` columns (50 sample area values)
- ✅ `NIST_SL (1)` column (NIST standard area values)

### Original Pattern Input Format

| Compound | PH-HC_1 | PH-HC_2 | ... | PH-HC_100 | NIST_1-100 (1) | NIST_1-100 (2) | NIST_1-100 (3) | NIST_1-100 (4) |
|----------|---------|---------|-----|-----------|----------------|----------------|----------------|----------------|
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

## Using the Streamlined Calculator

### Upload Your File

1. Go to https://www.httpsphenikaa-lipidomics-analysis.xyz/streamlined-calculator
2. Upload your Second List Lipidomic Excel file
3. The calculator will **automatically detect** the SL_ pattern
4. Processing begins immediately

### What Happens

```
📊 File Processing:
  ✅ Detected Second List pattern: SL_1 to SL_50
  ✅ Using sample index from database (150 entries)
  ✅ Sample SL_1 → NIST_SL (1)
  ✅ Sample SL_25 → NIST_SL (1)
  ✅ Sample SL_50 → NIST_SL (1)

📈 Calculations:
  ✅ Step 1: Ratio calculation (Sample Area / ISTD Area)
  ✅ Step 2: NIST calculation (Ratio × NIST Conc)
  ✅ Step 3: Agilent calculation (NIST Result × Volume Factor)

📥 Output:
  ✅ NIST Results sheet
  ✅ Agilent Results sheet
  ✅ Preview tables on webpage
```

## Code Changes

### streamlined_calculator_service.py

**Updated Methods:**

1. **`_load_sample_index()`**
   - Now loads from database first
   - Falls back to Excel if database unavailable
   - Supports 150+ sample entries

2. **`determine_sample_numbering()`**
   - Auto-detects SL_ vs PH-HC_ pattern
   - Returns pattern-specific NIST configurations
   - Uses database when available

3. **`find_matching_nist_column()`**
   - Database lookup priority
   - SL_ pattern: all samples → NIST_SL (1)
   - PH-HC_ pattern: range-based matching
   - Fallback to pattern matching

## Verification

### Check Database Contents

```python
from app import app, db
from models import SampleIndex, CompoundIndex

with app.app_context():
    # Check SL_ entries
    sl_samples = SampleIndex.query.filter(SampleIndex.sample.like('SL_%')).count()
    print(f"SL_ samples: {sl_samples}")  # Should be 50

    # Check total compounds
    total = CompoundIndex.query.count()
    print(f"Total compounds: {total}")  # Should be 891+
```

### Test Pattern Detection

```python
from streamlined_calculator_service import StreamlinedCalculatorService

service = StreamlinedCalculatorService()

# Test SL_ pattern
sl_columns = ['Compound', 'SL_1', 'SL_2', 'SL_50', 'NIST_SL (1)']
numbering = service.determine_sample_numbering(sl_columns)
print(numbering)
# Output: {'pattern_type': 'SL', 'nist_patterns': ['NIST_SL (1)'], ...}

# Test PH-HC_ pattern
ph_columns = ['Compound', 'PH-HC_1', 'PH-HC_100', 'NIST_1-100 (1)']
numbering = service.determine_sample_numbering(ph_columns)
print(numbering)
# Output: {'nist_patterns': ['NIST_1-100 (1)', ...], ...}
```

## Benefits

### ✅ Reusability
- Other projects can use the **same sample index pattern**
- No need to recreate mapping logic
- Database-driven configuration

### ✅ Flexibility
- Support for **multiple patterns** in one system
- Easy to add new patterns (just update database)
- Automatic pattern detection

### ✅ Consistency
- **Single source of truth** (database)
- All calculations use same mapping
- Reduces errors from manual configuration

## Adding New Patterns

To add a new pattern (e.g., "TL_" with 25 samples per NIST):

1. **Create migration script:**
   ```python
   for i in range(1, 26):
       sample_index = SampleIndex(
           sample=f'TL_{i}',
           paired_nist='NIST_TL (1)'
       )
       db.session.add(sample_index)
   ```

2. **Update pattern detection:**
   ```python
   elif 'TL_' in col_str:
       sample_pattern = 'TL'
   ```

3. **Add NIST mapping logic:**
   ```python
   if sample_pattern == 'TL':
       return {'nist_patterns': ['NIST_TL (1)']}
   ```

## Troubleshooting

### Issue: "No valid SL_ samples found"

**Solution:** Check your input file column names:
- ✅ Correct: `SL_1`, `SL_2`, etc.
- ❌ Incorrect: `sl_1`, `Sample_1`, `S_1`

### Issue: "Database lookup failed"

**Solution:** Run migration script:
```bash
python3 migrate_second_list_sample_index.py
```

### Issue: "NIST column not found"

**Solution:** Ensure NIST column is named exactly:
- ✅ Correct: `NIST_SL (1)` or `NIST_SL(1)`
- ❌ Incorrect: `NIST_SL_1`, `NIST (1)`

## Summary

🎉 **The system now supports**:
- ✅ 50 samples per 1 NIST (Second List pattern)
- ✅ 100 samples per 4 NIST (Original pattern)
- ✅ Database-driven sample indexing
- ✅ Automatic pattern detection
- ✅ 891+ compound mappings
- ✅ Easy pattern extensibility

**Database Tables:**
- `sample_index`: 150 entries (100 PH-HC_ + 50 SL_)
- `compound_index`: 891 entries (with ISTD mappings)

**Ready for production use! 🚀**
