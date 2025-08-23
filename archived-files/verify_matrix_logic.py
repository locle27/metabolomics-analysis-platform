#!/usr/bin/env python3

"""
Verify the matrix lookup logic works for ALL sample-compound combinations
No fallbacks allowed - must get correct values from the matrix
"""

def analyze_matrix_requirements():
    """
    Analyze what needs to be fixed for proper matrix lookup
    """
    print("🔍 MATRIX LOOKUP ANALYSIS")
    print("=" * 60)
    
    # Sample data from user's Excel file
    sample_data = {
        "compounds": ["AcylCarnitine 10:0", "AcylCarnitine 12:0", "AcylCarnitine 12:1"],
        "samples": ["PH-HC_1", "PH-HC_2", "PH-HC_5601", "PH-HC_5602"],
        "nist_columns": ["NIST_1-100 (1)", "NIST_1-100 (2)", "NIST_5601-5700 (1)", "NIST_5601-5700 (2)"],
        "known_values": {
            ("AcylCarnitine 10:0", "NIST_1-100 (1)"): 0.1769,
            ("AcylCarnitine 12:0", "NIST_1-100 (1)"): 0.0951,
            ("AcylCarnitine 12:0", "NIST_5601-5700 (1)"): "SHOULD_BE_FOUND_IN_EXCEL"
        }
    }
    
    print("📊 Matrix Structure:")
    print("  Rows = Compounds (AcylCarnitine 10:0, AcylCarnitine 12:0, ...)")
    print("  Columns = NIST references (NIST_1-100 (1), NIST_5601-5700 (1), ...)")
    print("  Cell = NIST value for that compound-sample combination")
    
    print(f"\n🧪 Test Cases Required:")
    test_cases = [
        ("PH-HC_1", "NIST_1-100 (1)", "AcylCarnitine 12:0", "0.0951"),
        ("PH-HC_2", "NIST_1-100 (1)", "AcylCarnitine 12:0", "0.0951"), 
        ("PH-HC_5601", "NIST_5601-5700 (1)", "AcylCarnitine 12:0", "VALUE_FROM_EXCEL"),
        ("PH-HC_5602", "NIST_5601-5700 (1)", "AcylCarnitine 12:0", "VALUE_FROM_EXCEL"),
    ]
    
    for sample, nist_col, compound, expected in test_cases:
        print(f"  {sample} → {nist_col} → {compound} = {expected}")
    
    print(f"\n❌ Current Problems:")
    print("  1. Sample mapping incomplete - not all PH-HC_* samples mapped to NIST columns")
    print("  2. Fallback values used when mapping fails")
    print("  3. NIST column matching might fail for spacing variations")
    print("  4. No verification that compound-NIST combinations exist")
    
    print(f"\n✅ Required Fixes:")
    print("  1. Complete sample-to-NIST mapping for ALL samples (1-100, 5601-5700, etc.)")
    print("  2. Bulletproof NIST column name matching (handle all spacing variations)")
    print("  3. Matrix bounds checking (verify compound exists, NIST column exists)")
    print("  4. Error reporting when data truly missing (not fallback)")
    print("  5. Debug logging to show exact matrix coordinates used")

if __name__ == "__main__":
    analyze_matrix_requirements()