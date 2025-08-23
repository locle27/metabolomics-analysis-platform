#!/usr/bin/env python3

"""
Script to fix the calculation function by removing old code
"""

def fix_calculation_function():
    """Remove old calculation code and clean up the function"""
    
    # Read the file
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the lines to remove (starting from the old calculation code)
    start_marker = "        # Convert ratio_sheet to safer format first\n"
    end_marker = "        print(\"Creating Excel output...\")\n"
    
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if line == start_marker:
            start_idx = i
        elif line == end_marker:
            end_idx = i
            break
    
    if start_idx is not None and end_idx is not None:
        print(f"Found old code from line {start_idx + 1} to {end_idx}")
        
        # Remove the old calculation code
        new_lines = lines[:start_idx] + ["        print(\"📊 Creating Excel output...\")\n"] + lines[end_idx + 1:]
        
        # Write the fixed file
        with open('app.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"✅ Removed {end_idx - start_idx} lines of old calculation code")
        print("✅ Fixed calculation function")
    else:
        print("❌ Could not find markers for old code removal")

if __name__ == "__main__":
    fix_calculation_function()