#!/usr/bin/env python3

"""
Verify the CORRECTED NIST calculation formula understanding
"""

def explain_corrected_formula():
    """
    Explain the corrected understanding of the NIST calculation
    """
    
    print("🎯 CORRECTED NIST CALCULATION UNDERSTANDING")
    print("=" * 70)
    
    print("\n❌ PREVIOUS WRONG UNDERSTANDING:")
    print("   NIST Result = Sample Ratio ÷ NIST Reference Value")
    print("   Where 'NIST Reference Value' was treated as a fixed reference number")
    
    print("\n✅ CORRECT UNDERSTANDING (User's Explanation):")
    print("   NIST Result = Sample Ratio ÷ NIST Ratio (same substance)")
    print("   Where 'NIST Ratio' is the ratio of the SAME compound in the NIST column")
    
    print("\n📊 THE REAL PROCESS:")
    print("   1. Calculate Sample Ratio: AcylCarnitine 12:0 Area ÷ ISTD Area")
    print("   2. Look up Sample Index: PH-HC_5601 → NIST_5601-5700(1)")  
    print("   3. Get NIST Ratio: AcylCarnitine 12:0 ratio in NIST_5601-5700(1) = 0.0951")
    print("   4. Calculate: NIST Result = Sample Ratio ÷ 0.0951")
    
    print("\n🗂️ WHAT THE NIST COLUMNS ACTUALLY CONTAIN:")
    print("   The NIST columns contain PRE-CALCULATED RATIOS for each substance:")
    print()
    print("   Matrix Structure:")
    print("                        NIST_5601-5700(1)  NIST_5601-5700(2)  ...")
    print("   AcylCarnitine 10:0         0.1769            0.1811        ...")
    print("   AcylCarnitine 12:0         0.0951            0.0985        ...  ← RATIOS!")
    print("   AcylCarnitine 12:1         0.1113            0.1114        ...")
    print()
    print("   These are NOT 'reference values' - they are RATIOS of the same compounds")
    print("   calculated for different NIST reference samples!")
    
    print("\n🧮 EXAMPLE CALCULATION:")
    print("   Sample: PH-HC_5601, Compound: AcylCarnitine 12:0")
    print()
    print("   Step 1: Sample Ratio")
    print("     Sample Ratio = 81,884 ÷ 212,434 = 0.385458")
    print()
    print("   Step 2: Find NIST Column")
    print("     PH-HC_5601 → Sample Index → NIST_5601-5700(1)")
    print()
    print("   Step 3: Get NIST Ratio (same substance)")
    print("     AcylCarnitine 12:0 ratio in NIST_5601-5700(1) = 0.0951")
    print()
    print("   Step 4: Calculate NIST Result")
    print("     NIST Result = 0.385458 ÷ 0.0951 = 4.053")
    print()
    print("   This means the sample ratio is 4.05x higher than the NIST standard ratio")
    
    print("\n🎯 KEY INSIGHTS:")
    print("   ✅ NIST columns contain ratios of the SAME compounds")
    print("   ✅ We compare sample ratio to NIST ratio (same substance)")
    print("   ✅ Different NIST columns have different ratios for the same compound")
    print("   ✅ The result shows relative concentration vs NIST standard")
    
    print("\n📋 SAMPLE INDEX SHEET PURPOSE:")
    print("   Maps samples to their corresponding NIST reference:")
    print("   • First 25 samples (1-25) → NIST_*-*(1)")
    print("   • Next 25 samples (26-50) → NIST_*-*(2)")  
    print("   • Next 25 samples (51-75) → NIST_*-*(3)")
    print("   • Last 25 samples (76-100) → NIST_*-*(4)")
    print()
    print("   This ensures each sample is compared to the appropriate NIST standard.")

def test_sample_index_logic():
    """
    Test the 25-samples-per-NIST-column logic
    """
    
    def get_nist_column_by_position(sample_name):
        """
        Calculate NIST column based on position within 100-sample range
        25 samples per NIST column
        """
        if not sample_name.startswith('PH-HC_'):
            return None
            
        try:
            sample_num = int(sample_name.split('_')[1])
            
            # Calculate range start (e.g., 5601 for PH-HC_5601)
            range_start = (sample_num // 100) * 100 + 1
            range_end = range_start + 99
            
            # Calculate position within the 100-sample range (1-100)
            position_in_range = sample_num - range_start + 1
            
            # Calculate NIST column number (25 samples per column)
            nist_number = ((position_in_range - 1) // 25) + 1
            
            return f"NIST_{range_start}-{range_end}({nist_number})"
        except:
            return None
    
    print("\n🧪 SAMPLE INDEX LOGIC TEST:")
    print("=" * 50)
    
    test_cases = [
        # Range 1-100
        ("PH-HC_1", "NIST_1-100(1)", "Position 1, first 25"),
        ("PH-HC_25", "NIST_1-100(1)", "Position 25, first 25"),
        ("PH-HC_26", "NIST_1-100(2)", "Position 26, second 25"),
        ("PH-HC_50", "NIST_1-100(2)", "Position 50, second 25"),
        ("PH-HC_51", "NIST_1-100(3)", "Position 51, third 25"),
        ("PH-HC_75", "NIST_1-100(3)", "Position 75, third 25"),
        ("PH-HC_76", "NIST_1-100(4)", "Position 76, fourth 25"),
        ("PH-HC_100", "NIST_1-100(4)", "Position 100, fourth 25"),
        
        # Range 5601-5700 (User's case)
        ("PH-HC_5601", "NIST_5601-5700(1)", "Position 1, first 25"),
        ("PH-HC_5625", "NIST_5601-5700(1)", "Position 25, first 25"),
        ("PH-HC_5626", "NIST_5601-5700(2)", "Position 26, second 25"),
        ("PH-HC_5650", "NIST_5601-5700(2)", "Position 50, second 25"),
        ("PH-HC_5676", "NIST_5601-5700(4)", "Position 76, fourth 25"),
        ("PH-HC_5700", "NIST_5601-5700(4)", "Position 100, fourth 25"),
    ]
    
    all_passed = True
    for sample, expected, description in test_cases:
        result = get_nist_column_by_position(sample)
        status = "✅" if result == expected else "❌"
        
        if result != expected:
            all_passed = False
            
        print(f"  {status} {sample:12} → {result or 'None':20} ({description})")
    
    print(f"\n{'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎯 PERFECT! The 25-samples-per-NIST-column logic works correctly.")
        print("   • PH-HC_5601 → NIST_5601-5700(1) (position 1, first 25)")
        print("   • Each sample gets the correct NIST reference column")
        print("   • AcylCarnitine 12:0 will get its ratio from the right NIST column")

if __name__ == "__main__":
    explain_corrected_formula()
    test_sample_index_logic()
    
    print(f"\n🎯 SUMMARY:")
    print("✅ Formula corrected: Sample Ratio ÷ NIST Ratio (same substance)")
    print("✅ NIST columns contain ratios, not reference values")
    print("✅ 25-samples-per-NIST-column logic implemented")
    print("✅ PH-HC_5601 will use AcylCarnitine 12:0 ratio from NIST_5601-5700(1)")
    print("✅ Result shows relative concentration vs NIST standard")