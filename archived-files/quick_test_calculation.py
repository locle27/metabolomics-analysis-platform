#!/usr/bin/env python3

"""
Quick test of the corrected calculation logic
"""

def test_calculation():
    """Test the NIST calculation with known values"""
    print("🧮 TESTING CORRECTED CALCULATION")
    print("=" * 40)
    
    # From the analysis, we know:
    # - Area value: 212159.810425247
    # - Original ratio: 0.9987108488
    # - Expected NIST result: 5.645936475
    
    area_value = 212159.810425247
    istd_area = 212434.0  # Calculated from area/ratio
    
    # Calculate ratio
    calculated_ratio = area_value / istd_area
    print(f"Area: {area_value}")
    print(f"ISTD: {istd_area}")
    print(f"Calculated ratio: {calculated_ratio}")
    print(f"Original ratio: 0.9987108488")
    print(f"Ratio match: {abs(calculated_ratio - 0.9987108488) < 0.001}")
    
    # Now for NIST calculation, we need the NIST reference value
    # Let's assume NIST reference = 0.1769 (common value)
    nist_reference = 0.1769
    calculated_nist = calculated_ratio / nist_reference
    
    print(f"\nNIST reference: {nist_reference}")
    print(f"Calculated NIST: {calculated_nist}")
    print(f"Expected NIST: 5.645936475")
    print(f"NIST match: {abs(calculated_nist - 5.645936475) < 0.01}")
    
    # If this doesn't match, try different NIST reference values
    expected_nist = 5.645936475
    correct_nist_ref = calculated_ratio / expected_nist
    print(f"\nCorrect NIST reference should be: {correct_nist_ref}")

if __name__ == "__main__":
    test_calculation()