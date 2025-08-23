#!/usr/bin/env python3

"""
Simple import script for Sample Index and Compound Index reference data
Uses minimal dependencies and direct database operations
"""

import pandas as pd
import sys
import os
import sqlite3
import psycopg2
from urllib.parse import urlparse

def get_database_connection():
    """Get database connection based on DATABASE_URL"""
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///metabolomics.db')
    
    if DATABASE_URL.startswith('postgres://') or DATABASE_URL.startswith('postgresql://'):
        # PostgreSQL connection
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        
        parsed = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password
        )
        return conn, 'postgresql'
    else:
        # SQLite connection
        db_path = DATABASE_URL.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        return conn, 'sqlite'

def create_tables(conn, db_type):
    """Create the reference data tables"""
    cursor = conn.cursor()
    
    if db_type == 'postgresql':
        # PostgreSQL table creation
        sample_index_sql = """
        CREATE TABLE IF NOT EXISTS sample_index (
            id SERIAL PRIMARY KEY,
            sample VARCHAR(255) NOT NULL UNIQUE,
            paired_nist VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_sample_index_sample ON sample_index(sample);
        """
        
        compound_index_sql = """
        CREATE TABLE IF NOT EXISTS compound_index (
            id SERIAL PRIMARY KEY,
            compound VARCHAR(255) NOT NULL UNIQUE,
            istd VARCHAR(255) NOT NULL,
            conc_nm FLOAT,
            response_factor FLOAT DEFAULT 1.0,
            nist_conc_nm FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_compound_index_compound ON compound_index(compound);
        """
    else:
        # SQLite table creation
        sample_index_sql = """
        CREATE TABLE IF NOT EXISTS sample_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample TEXT NOT NULL UNIQUE,
            paired_nist TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_sample_index_sample ON sample_index(sample);
        """
        
        compound_index_sql = """
        CREATE TABLE IF NOT EXISTS compound_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            compound TEXT NOT NULL UNIQUE,
            istd TEXT NOT NULL,
            conc_nm REAL,
            response_factor REAL DEFAULT 1.0,
            nist_conc_nm REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_compound_index_compound ON compound_index(compound);
        """
    
    cursor.execute(sample_index_sql)
    cursor.execute(compound_index_sql)
    conn.commit()
    print("✅ Database tables created/verified")

def import_sample_index_data(conn, db_type, file_path):
    """Import Sample Index data from Excel file"""
    print("📊 Reading Sample Index data from Excel...")
    
    df = pd.read_excel(file_path, sheet_name='Sample index')
    print(f"Found {len(df)} sample index records")
    
    cursor = conn.cursor()
    
    # Clear existing data
    print("🗑️ Clearing existing Sample Index data...")
    cursor.execute("DELETE FROM sample_index")
    conn.commit()
    
    # Import new data
    imported_count = 0
    for _, row in df.iterrows():
        if db_type == 'postgresql':
            cursor.execute(
                "INSERT INTO sample_index (sample, paired_nist) VALUES (%s, %s)",
                (str(row['sample']).strip(), str(row['paired_nist']).strip())
            )
        else:
            cursor.execute(
                "INSERT INTO sample_index (sample, paired_nist) VALUES (?, ?)",
                (str(row['sample']).strip(), str(row['paired_nist']).strip())
            )
        imported_count += 1
    
    conn.commit()
    print(f"✅ Imported {imported_count} Sample Index records")
    
    # Verify import
    cursor.execute("SELECT COUNT(*) FROM sample_index")
    total_samples = cursor.fetchone()[0]
    print(f"🔍 Verification: {total_samples} sample index records in database")
    
    return imported_count

def import_compound_index_data(conn, db_type, file_path):
    """Import Compound Index data from Excel file"""
    print("📊 Reading Compound Index data from Excel...")
    
    df = pd.read_excel(file_path, sheet_name='Compound index')
    print(f"Found {len(df)} compound index records")
    print(f"Columns: {list(df.columns)}")
    
    cursor = conn.cursor()
    
    # Clear existing data
    print("🗑️ Clearing existing Compound Index data...")
    cursor.execute("DELETE FROM compound_index")
    conn.commit()
    
    # Import new data
    imported_count = 0
    for _, row in df.iterrows():
        compound = str(row['Compound']).strip()
        istd = str(row['ISTD']).strip()
        conc_nm = float(row['Conc. (nM)']) if pd.notna(row['Conc. (nM)']) else None
        response_factor = float(row['Response factor']) if pd.notna(row['Response factor']) else 1.0
        nist_conc_nm = float(row['NIST Conc. (nM)']) if pd.notna(row['NIST Conc. (nM)']) else None
        
        if db_type == 'postgresql':
            cursor.execute(
                "INSERT INTO compound_index (compound, istd, conc_nm, response_factor, nist_conc_nm) VALUES (%s, %s, %s, %s, %s)",
                (compound, istd, conc_nm, response_factor, nist_conc_nm)
            )
        else:
            cursor.execute(
                "INSERT INTO compound_index (compound, istd, conc_nm, response_factor, nist_conc_nm) VALUES (?, ?, ?, ?, ?)",
                (compound, istd, conc_nm, response_factor, nist_conc_nm)
            )
        imported_count += 1
    
    conn.commit()
    print(f"✅ Imported {imported_count} Compound Index records")
    
    # Verify import
    cursor.execute("SELECT COUNT(*) FROM compound_index")
    total_compounds = cursor.fetchone()[0]
    print(f"🔍 Verification: {total_compounds} compound index records in database")
    
    return imported_count

def main():
    """Main import function"""
    print("🚀 QUANTITATIVE ANALYSIS REFERENCE DATA IMPORT")
    print("=" * 60)
    
    file_path = 'Calculate alysis.xlsx'
    
    if not os.path.exists(file_path):
        print(f"❌ Error: Excel file not found: {file_path}")
        sys.exit(1)
    
    try:
        # Get database connection
        conn, db_type = get_database_connection()
        print(f"✅ Connected to {db_type} database")
        
        # Create tables
        create_tables(conn, db_type)
        
        # Import Sample Index data
        sample_count = import_sample_index_data(conn, db_type, file_path)
        
        # Import Compound Index data  
        compound_count = import_compound_index_data(conn, db_type, file_path)
        
        print(f"\n🎉 IMPORT COMPLETE!")
        print(f"📊 Sample Index records: {sample_count}")
        print(f"🧪 Compound Index records: {compound_count}")
        print(f"\n✅ Reference data is now available for calculation tool")
        
        # Show sample data
        print(f"\n📋 Sample data preview:")
        cursor = conn.cursor()
        cursor.execute("SELECT sample, paired_nist FROM sample_index LIMIT 5")
        samples = cursor.fetchall()
        for sample, paired_nist in samples:
            print(f"  {sample} → {paired_nist}")
        
        cursor.execute("SELECT compound, istd, response_factor FROM compound_index LIMIT 5")
        compounds = cursor.fetchall()
        print(f"\n🧪 Compound data preview:")
        for compound, istd, rf in compounds:
            print(f"  {compound} | ISTD: {istd} | RF: {rf}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()