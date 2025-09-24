#!/usr/bin/env python3
"""
Quick script to fix empty if/except/try blocks left by emoji cleanup
"""

import re

def fix_empty_blocks(file_path):
    """Fix empty code blocks in Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # Check if this line ends with : and next few lines are empty/whitespace only
        if line.strip().endswith(':'):
            j = i + 1
            found_content = False
            empty_line_count = 0
            
            # Look ahead for content or next statement
            while j < len(lines):
                next_line = lines[j].strip()
                
                if not next_line:  # Empty line
                    empty_line_count += 1
                    j += 1
                    continue
                
                # Check if we found indented content
                if next_line and len(lines[j]) > len(lines[j].lstrip()) and len(lines[j].lstrip()) > 0:
                    # This is indented content
                    if not any(keyword in next_line.lower() for keyword in ['else:', 'elif', 'except', 'finally', 'def ', 'class ']):
                        found_content = True
                    break
                else:
                    # Found unindented line or keyword, no content in block
                    break
            
            # If no content found and we have empty lines, add 'pass'
            if not found_content and empty_line_count > 0:
                # Get indentation level
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(' ' * (indent + 4) + 'pass  # Empty block fixed')
        
        i += 1
    
    # Write fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print(f"Fixed empty blocks in {file_path}")

if __name__ == "__main__":
    fix_empty_blocks("/mnt/c/Users/T14/Desktop/metabolomics-project/app.py")