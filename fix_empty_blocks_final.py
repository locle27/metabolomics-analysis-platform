#!/usr/bin/env python3
"""Fix all empty if/else/for/while blocks in streamlined_calculator_service.py"""

import re

def fix_empty_blocks():
    with open('streamlined_calculator_service.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        fixed_lines.append(line + '\n')
        
        # Check if this line ends with : (if, else, for, while, etc.)
        if line.strip().endswith(':'):
            current_indent = len(line) - len(line.lstrip())
            j = i + 1
            
            # Skip empty lines and comments
            while j < len(lines) and (lines[j].strip() == '' or lines[j].strip().startswith('#')):
                fixed_lines.append(lines[j])
                j += 1
            
            # Check if we need to add pass
            if j < len(lines):
                next_line = lines[j]
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If next line has same or less indentation, this block is empty
                if next_indent <= current_indent and next_line.strip() not in ['pass', '']:
                    # Add pass statement
                    pass_line = ' ' * (current_indent + 4) + 'pass  # Fixed empty block\n'
                    fixed_lines.append(pass_line)
            elif j >= len(lines):
                # End of file, add pass
                pass_line = ' ' * (current_indent + 4) + 'pass  # Fixed empty block\n'
                fixed_lines.append(pass_line)
            
            i = j - 1 if j < len(lines) else i
        
        i += 1
    
    # Write back
    with open('streamlined_calculator_service.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Fixed all empty blocks in streamlined_calculator_service.py")

if __name__ == '__main__':
    fix_empty_blocks()