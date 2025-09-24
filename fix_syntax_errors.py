#!/usr/bin/env python3
"""Fix empty if/except blocks that cause IndentationError"""

import re

def fix_syntax_errors():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix empty if statements followed by else
    content = re.sub(r'(\s+if .+:)\s*\n\s*\n(\s+else:)', r'\1\n\2                pass  # Fixed empty if block\n\3', content)
    
    # Fix empty if statements at end of blocks
    content = re.sub(r'(\s+if .+:)\s*\n\s*\n(\s+)(?=[a-zA-Z])', r'\1\n\2    pass  # Fixed empty if block\n\3', content)
    
    # Fix empty except blocks
    content = re.sub(r'(\s+except[^:]*:)\s*\n\s*\n(\s+)(?=[a-zA-Z])', r'\1\n\2    pass  # Fixed empty except block\n\3', content)
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for empty if/except blocks
        if (line.strip().endswith(':') and 
            ('if ' in line or 'except' in line or 'try:' in line) and
            i + 1 < len(lines)):
            
            # Look ahead to see if next non-empty line has same or less indentation
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
                
            if j < len(lines):
                current_indent = len(line) - len(line.lstrip())
                next_line = lines[j]
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If next line has same or less indentation, add pass
                if next_indent <= current_indent and next_line.strip() not in ['pass', '']:
                    fixed_lines.append(line)
                    # Add empty lines we skipped
                    for k in range(i + 1, j):
                        if lines[k].strip() == '':
                            fixed_lines.append(lines[k])
                    # Add pass statement
                    fixed_lines.append(' ' * (current_indent + 4) + 'pass  # Fixed empty block')
                    i = j - 1
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
        
        i += 1
    
    # Write fixed content
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print("Fixed syntax errors in app.py")

if __name__ == '__main__':
    fix_syntax_errors()