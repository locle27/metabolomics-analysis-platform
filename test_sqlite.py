#!/usr/bin/env python3
"""
Test SQLite Database Connection
"""

import sqlite3
import os

print("🔍 TESTING SQLITE DATABASE")
print("=" * 35)

try:
    # Check if file exists
    if os.path.exists('metabolomics_fast.db'):
        size_mb = os.path.getsize('metabolomics_fast.db') / (1024*1024)
        print(f"✅ Database file exists: {size_mb:.1f} MB")
        
        # Try to connect
        conn = sqlite3.connect('metabolomics_fast.db')
        print("✅ Connection successful")
        
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 Tables: {[t[0] for t in tables]}")
        
        # Count records
        if ('main_lipids',) in tables:
            cursor.execute("SELECT COUNT(*) FROM main_lipids")
            lipid_count = cursor.fetchone()[0]
            print(f"📈 Main lipids: {lipid_count}")
            
            # Sample data
            cursor.execute("SELECT lipid_name FROM main_lipids LIMIT 3")
            samples = cursor.fetchall()
            print(f"📋 Sample lipids: {[s[0] for s in samples]}")
        
        conn.close()
        print("✅ Database is working correctly!")
        
    else:
        print("❌ Database file not found!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("🔧 Solution: Recreate the database")
    print("   The SQLite file may be corrupted.")