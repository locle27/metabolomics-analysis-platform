#!/usr/bin/env python3
"""
Final fix for all indentation issues caused by commenting out debug prints
"""

import re

def fix_syntax_issues(file_path):
    """Fix all indentation and syntax issues"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix empty except blocks
    content = re.sub(r'(\s+except\s+[^:]+:)\s*\n\s*\n\s*(#[^\n]*\n)?\s*([^ \n#])', 
                     r'\1\n\2            pass  # Empty except block\n\3', content)
    
    # Fix empty if blocks  
    content = re.sub(r'(\s+if\s+[^:]+:)\s*\n\s*\n\s*(#[^\n]*\n)?\s*(else:|elif|except|def|class|return|if|for|while)', 
                     r'\1\n\2            pass  # Empty if block\n\3', content)
    
    # Fix empty try blocks
    content = re.sub(r'(\s+try:)\s*\n\s*\n\s*(#[^\n]*\n)?\s*(except|finally)', 
                     r'\1\n\2            pass  # Empty try block\n\3', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Applied final syntax fixes to {file_path}")

if __name__ == "__main__":
    fix_syntax_issues("/mnt/c/Users/T14/Desktop/metabolomics-project/app.py")