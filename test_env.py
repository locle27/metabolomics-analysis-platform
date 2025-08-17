#!/usr/bin/env python3
"""Test Railway environment before deployment"""

import os
import sys

print("🧪 TESTING RAILWAY ENVIRONMENT")
print("=" * 40)

# Test 1: Python version
print(f"Python: {sys.version}")
if sys.version_info >= (3, 8):
    print("✅ Python version OK")
else:
    print("❌ Python version too old")

# Test 2: Essential imports
try:
    import flask
    print(f"✅ Flask {flask.__version__} available")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")

try:
    import gunicorn
    print(f"✅ Gunicorn available")
except ImportError as e:
    print(f"❌ Gunicorn import failed: {e}")

# Test 3: Environment variables
print(f"\nEnvironment:")
print(f"PORT: {os.getenv('PORT', 'NOT SET')}")
print(f"DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') else 'NOT SET'}")

# Test 4: File system
print(f"\nFiles in directory:")
for f in sorted(os.listdir('.')):
    if not f.startswith('.'):
        print(f"  {f}")

print("\n🧪 Environment test complete")