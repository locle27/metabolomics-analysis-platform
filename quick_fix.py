#!/usr/bin/env python3
import re

# Read the file
with open('app.py', 'r') as f:
    content = f.read()

# Fix pattern: if condition:\n\n            else:
content = re.sub(r'(\s+if [^:]+:)\s*\n\s*\n(\s+else:)', r'\1\n\2                pass  # Fixed\n\3', content)

# Fix pattern: if condition:\n\n        (next statement at same level)
content = re.sub(r'(\s+if [^:]+:)\s*\n\s*\n(\s+)([a-zA-Z])', r'\1\n\2    pass  # Fixed\n\3\4', content)

# Write back
with open('app.py', 'w') as f:
    f.write(content)

print("Fixed empty if blocks")