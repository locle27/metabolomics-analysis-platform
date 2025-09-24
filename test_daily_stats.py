#!/usr/bin/env python3
"""Test the daily statistics endpoint to ensure SQLAlchemy is properly initialized"""

import requests
from datetime import datetime

# Test the daily statistics endpoint
url = "http://localhost:5000/api/daily-statistics"
params = {"date": "2025-09-04"}

print("Testing daily statistics endpoint...")
print(f"URL: {url}")
print(f"Params: {params}")

try:
    response = requests.get(url, params=params)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success! Daily statistics loaded properly")
        print(f"Response: {data}")
    else:
        print("❌ Error response:")
        print(response.text)
        
except Exception as e:
    print(f"❌ Request failed: {e}")