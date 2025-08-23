#!/usr/bin/env python3

"""
Verify that the NIST column matching fix works correctly
"""

def test_nist_matching():
    """Test NIST column matching logic"""
    
    # Test cases simulating different column name formats
    test_columns = [
        "NIST_1-100 (1)",    # With space before parenthesis
        "NIST_1-100(1)",     # Without space
        "NIST_1-100 (1) ",   # With trailing space
        " NIST_1-100 (1)",   # With leading space
        "NIST_1-100 (2)",    # Different number
        "NIST_5701-5800 (1)" # Different range
    ]
    
    # Target column names to match
    target_names = [
        "NIST_1-100 (1)",
        "NIST_1-100(1)"
    ]
    
    print("🧪 Testing NIST column matching logic:")
    print("=" * 50)
    
    for target in target_names:
        print(f"\n🎯 Looking for: '{target}'")
        
        for col in test_columns:
            col_str = str(col).strip()
            target_str = str(target).strip()
            
            # Test exact match
            exact_match = col_str == target_str
            
            # Test normalized match (remove spaces)
            normalized_match = col_str.replace(' ', '') == target_str.replace(' ', '')
            
            # Test pattern match
            pattern_match = ('1-100' in col_str and '1-100' in target_str and 
                           '(1)' in col_str and '(1)' in target_str)
            
            # Combined match (as implemented in fix)
            matches = (exact_match or normalized_match or pattern_match)
            
            print(f"  Column: '{col}'")
            print(f"    Exact match: {exact_match}")
            print(f"    Normalized match: {normalized_match}")
            print(f"    Pattern match: {pattern_match}")
            print(f"    ✅ MATCHES" if matches else "    ❌ No match")
            print()

    print("\n📝 Summary:")
    print("The improved matching logic should handle:")
    print("- Exact matches")
    print("- Spaces before/after parentheses")
    print("- Leading/trailing spaces")
    print("- Pattern-based matching for NIST_1-100 (1) variations")

if __name__ == "__main__":
    test_nist_matching()