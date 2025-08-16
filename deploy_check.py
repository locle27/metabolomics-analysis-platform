#!/usr/bin/env python3
"""
Pre-deployment Validation Script
Checks all critical files and configurations before Railway deployment
"""

import os
import sys
import json
from pathlib import Path

def check_file_exists(filename, critical=True):
    """Check if a file exists"""
    if os.path.exists(filename):
        print(f"✅ {filename} - EXISTS")
        return True
    else:
        status = "❌ CRITICAL" if critical else "⚠️ OPTIONAL"
        print(f"{status} {filename} - MISSING")
        return not critical

def check_python_syntax(filename):
    """Check Python file syntax"""
    if not os.path.exists(filename):
        return False
    
    try:
        with open(filename, 'r') as f:
            compile(f.read(), filename, 'exec')
        print(f"✅ {filename} - SYNTAX OK")
        return True
    except SyntaxError as e:
        print(f"❌ {filename} - SYNTAX ERROR: {e}")
        return False

def check_requirements():
    """Check requirements.txt format"""
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt - MISSING")
        return False
    
    with open('requirements.txt', 'r') as f:
        lines = f.readlines()
    
    required_packages = ['Flask', 'gunicorn', 'psycopg2-binary', 'SQLAlchemy']
    found_packages = []
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            package = line.split('==')[0]
            found_packages.append(package)
    
    missing = [pkg for pkg in required_packages if pkg not in found_packages]
    
    if missing:
        print(f"⚠️ requirements.txt - MISSING PACKAGES: {', '.join(missing)}")
    else:
        print("✅ requirements.txt - ALL CRITICAL PACKAGES FOUND")
    
    print(f"   Found packages: {', '.join(found_packages[:5])}...")
    return len(missing) == 0

def check_railway_config():
    """Check Railway configuration"""
    if not os.path.exists('railway.json'):
        print("❌ railway.json - MISSING")
        return False
    
    try:
        with open('railway.json', 'r') as f:
            config = json.load(f)
        
        start_command = config.get('deploy', {}).get('startCommand', '')
        healthcheck_path = config.get('deploy', {}).get('healthcheckPath', '')
        
        print(f"✅ railway.json - VALID JSON")
        print(f"   Start command: {start_command}")
        print(f"   Healthcheck path: {healthcheck_path}")
        
        # Check if start command references existing file
        if 'app_bulletproof_fixed:app' in start_command:
            if os.path.exists('app_bulletproof_fixed.py'):
                print("✅ railway.json - START COMMAND REFERENCES EXISTING FILE")
                return True
            else:
                print("❌ railway.json - START COMMAND REFERENCES MISSING FILE")
                return False
        else:
            print("⚠️ railway.json - START COMMAND MIGHT BE INCORRECT")
            return True
            
    except json.JSONDecodeError as e:
        print(f"❌ railway.json - INVALID JSON: {e}")
        return False

def check_environment_template():
    """Check environment configuration"""
    if os.path.exists('.env.production'):
        print("✅ .env.production - EXISTS (template)")
    else:
        print("⚠️ .env.production - MISSING (template)")
    
    if os.path.exists('.env.example'):
        print("✅ .env.example - EXISTS")
    else:
        print("⚠️ .env.example - MISSING")

def main():
    """Run all validation checks"""
    print("🔍 PRE-DEPLOYMENT VALIDATION")
    print("=" * 50)
    
    all_good = True
    
    # Critical files
    print("\n📁 CRITICAL FILES:")
    critical_files = [
        'app_bulletproof_fixed.py',
        'requirements.txt',
        'railway.json'
    ]
    
    for file in critical_files:
        if not check_file_exists(file, critical=True):
            all_good = False
    
    # Optional files
    print("\n📁 OPTIONAL FILES:")
    optional_files = [
        'models_postgresql_optimized.py',
        'email_auth_production.py',
        'Procfile'
    ]
    
    for file in optional_files:
        check_file_exists(file, critical=False)
    
    # Python syntax
    print("\n🐍 PYTHON SYNTAX:")
    python_files = [
        'app_bulletproof_fixed.py',
        'models_postgresql_optimized.py',
        'email_auth_production.py'
    ]
    
    for file in python_files:
        if os.path.exists(file):
            if not check_python_syntax(file):
                all_good = False
    
    # Requirements
    print("\n📦 REQUIREMENTS:")
    if not check_requirements():
        all_good = False
    
    # Railway config
    print("\n🚂 RAILWAY CONFIG:")
    if not check_railway_config():
        all_good = False
    
    # Environment
    print("\n🔧 ENVIRONMENT:")
    check_environment_template()
    
    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 ALL CRITICAL CHECKS PASSED!")
        print("✅ Ready for Railway deployment")
        print("\n📋 DEPLOYMENT STEPS:")
        print("1. Commit and push changes to Git")
        print("2. Deploy to Railway")
        print("3. Set environment variables in Railway dashboard:")
        print("   - DATABASE_URL")
        print("   - SECRET_KEY")
        print("   - FLASK_ENV=production")
        print("4. Check healthcheck at: /health")
        print("5. Monitor deployment logs")
    else:
        print("❌ CRITICAL ISSUES FOUND!")
        print("🛠️ Fix the issues above before deploying")
        sys.exit(1)

if __name__ == '__main__':
    main()