#!/usr/bin/env python3
"""
Fix indentation issues caused by removing print statements
"""

import re

def fix_empty_blocks(file_path):
    """Fix empty code blocks by adding pass statements where needed"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # Check if this line starts a code block (ends with :)
        if line.strip().endswith(':') and line.strip() not in ['"""', "'''"]:
            # Look ahead to see if block is empty
            j = i + 1
            indent_level = len(line) - len(line.lstrip())
            expected_indent = indent_level + 4
            found_content = False
            
            # Skip empty lines and comments
            while j < len(lines):
                next_line = lines[j]
                next_stripped = next_line.strip()
                
                if not next_stripped:  # Empty line
                    j += 1
                    continue
                
                if next_stripped.startswith('# Debug print removed'):  # Our comment
                    j += 1
                    continue
                
                # Check if we have proper indented content
                if len(next_line) - len(next_line.lstrip()) == expected_indent:
                    # This is properly indented content
                    found_content = True
                    break
                elif len(next_line) - len(next_line.lstrip()) < expected_indent:
                    # This is dedented (end of block)
                    break
                else:
                    # More indented, keep looking
                    j += 1
                    continue
            
            # If no content found, add pass statement
            if not found_content:
                pass_line = ' ' * expected_indent + 'pass  # Empty block\n'
                fixed_lines.append(pass_line)
        
        i += 1
    
    # Write fixed file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed indentation issues in {file_path}")

if __name__ == "__main__":
    fix_empty_blocks("/mnt/c/Users/T14/Desktop/metabolomics-project/app.py")