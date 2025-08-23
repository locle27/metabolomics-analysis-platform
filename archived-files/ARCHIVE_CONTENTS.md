# ARCHIVED FILES - PROJECT CLEANUP

This folder contains files that were moved during project cleanup to keep the main project directory clean and focused.

## ✅ ARCHIVED FILES SUMMARY

### **Debug & Testing Scripts (38 files)**
- `analyze_data_files.py` - Data analysis utilities
- `analyze_excel.py` - Excel file analysis tools
- `analyze_nist_calculation.py` - NIST calculation debugging
- `check_and_fix_database.py` - Database repair utilities
- `check_sample_index.py` - Sample index validation
- `create_ratio_preview_table.py` - Preview table generators
- `create_reference_tables.py` - Reference data utilities
- `debug_calculation.py` - Calculation debugging tools
- `debug_nist_matching.py` - NIST matching debugging
- `debug_sample_index.py` - Sample index debugging
- `extract_nist_ratios.py` - NIST ratio extraction
- `extract_real_sample_data.py` - Sample data extraction
- `fix_calculation.py` - Calculation fix utilities
- `fix_calculation_logic.py` - Logic fix utilities
- `fix_network_errors.py` - Network error fixes
- `fix_nist_retrieval.py` - NIST retrieval fixes
- `fix_syntax_error.py` - Syntax error fixes
- `fixed_ratio_preview.py` - Fixed preview utilities
- `get_nist_reference.py` - NIST reference utilities
- `import_reference_data.py` - Data import utilities
- `import_reference_simple.py` - Simple import utilities
- `migrate_reference_tables.py` - Migration utilities
- `quick_test_calculation.py` - Quick testing tools
- `ratio_preview_service.py` - Preview service (old)
- `ratio_preview_service_fixed.py` - Preview service (fixed)
- `ratio_sheet_calculator.py` - Ratio calculation tools
- `read_real_nist_areas.py` - NIST area reading tools
- `test_bulletproof_matrix.py` - Matrix testing
- `test_nan_fix.py` - NaN error testing
- `test_ondemand_system.py` - On-demand system testing
- `test_range_fix.py` - Range fix testing
- `ultra_fix_nan.py` - Advanced NaN fixes
- `verify_compound_search_fix.py` - Compound search verification
- `verify_corrected_formula.py` - Formula correction verification
- `verify_fix.py` - General fix verification
- `verify_matrix_logic.py` - Matrix logic verification
- `verify_nist_fix.py` - NIST fix verification

### **Old Documentation (10 files)**
- `ADMIN_QUICK_REFERENCE.md` - Admin reference guide
- `BACKUP_STATUS.md` - Backup status documentation
- `COMPLETE_RATIO_SYSTEM.md` - Complete ratio system docs
- `COMPLETE_USER_GUIDE.md` - Complete user guide
- `FIXED_SAMPLE_NORMALIZATION.md` - Sample normalization fixes
- `NIST_PREVIEW_TABLE_EXPLANATION.md` - NIST table explanations
- `PROJECT_CLEANUP_SUMMARY.md` - Project cleanup summaries
- `STREAMLINED_CALCULATOR_COMPLETE.md` - Streamlined calculator docs
- `ULTRA_DETAILED_CALCULATION_FEATURE.md` - Detailed calculation docs
- `fix_nist_calculation.md` - NIST calculation fix notes

### **Test Images & Screenshots (6 files)**
- `NIST.png` - NIST calculation screenshot
- `error.png` - Error screenshot
- `excel.png` - Excel comparison screenshot  
- `formula.png` - Formula documentation screenshot
- `new-error.png` - New error screenshot
- `result-example1.png` - Result example screenshot

### **Backup & Temporary Files (5 files)**
- `app.py.backup` - App backup before cleanup
- `fixed_ratio_preview_table.csv` - Fixed preview table data
- `ratio_preview_table.csv` - Original preview table data
- `real_sample_data.json` - Real sample data backup
- `ondemand_system_instructions.json` - System instructions backup

### **Test Excel Files (1 file)**
- `web.xlsx` - Web comparison test file

**Note**: Some Excel files (`Book1.xlsx`, `Calculate_alysis.xlsx`, `area-compound.xlsx`) were locked by Excel and remain in the main directory but are no longer needed for the core system.

## ⚠️ IMPORTANT
- **These files are archived and NOT used by the production system**
- **The main application runs without any of these files**
- **Safe to keep for reference or delete if storage space is needed**
- **DO NOT move these files back to the main directory**

## 🎯 CURRENT ACTIVE SYSTEM
The main project now uses only:
- `streamlined_calculator_service.py` - Core calculation engine
- `app.py` - Main Flask application  
- `models.py` - Database models
- `dual_chart_service.py` - Chart generation
- Core database files: `Ratio-database.xlsx`, `sample-index.xlsx`, `compound-index.xlsx`
- Templates in `templates/` folder
- Static assets in `static/` folder

**Total archived: 59+ files moved to keep the project clean and focused.**