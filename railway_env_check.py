#!/usr/bin/env python3
"""
Railway Environment Variables Checker
Run this to see what environment variables Railway needs
"""

import os

def check_railway_env():
    """Check required environment variables for Railway"""
    print("🔧 REQUIRED RAILWAY ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    # Essential variables for Railway
    required_vars = {
        # Database (Railway auto-provides this)
        'DATABASE_URL': 'Auto-provided by Railway PostgreSQL service',
        
        # Flask Configuration
        'SECRET_KEY': 'Strong secret key for Flask sessions',
        'FLASK_ENV': 'Set to "production"',
        'FLASK_DEBUG': 'Set to "False"',
        
        # Custom Domain
        'CUSTOM_DOMAIN': 'httpsphenikaa-lipidomics-analysis.xyz',
        'PROD_OAUTH_BASE_URL': 'https://httpsphenikaa-lipidomics-analysis.xyz',
        
        # Google OAuth
        'GOOGLE_CLIENT_ID': 'Your Google OAuth Client ID',
        'GOOGLE_CLIENT_SECRET': 'Your Google OAuth Client Secret',
        
        # Email Configuration
        'MAIL_SERVER': 'smtp.gmail.com',
        'MAIL_PORT': '587',
        'MAIL_USE_TLS': 'True',
        'MAIL_USERNAME': 'Your Gmail address',
        'MAIL_PASSWORD': 'Your Gmail app password',
        'MAIL_DEFAULT_SENDER': 'Your Gmail address'
    }
    
    print("Copy these to Railway Dashboard → Your Service → Variables:\n")
    
    for var, description in required_vars.items():
        if var == 'DATABASE_URL':
            print(f"✅ {var} = (Auto-provided by Railway)")
        elif var in ['SECRET_KEY']:
            print(f"🔑 {var} = your-strong-secret-key-here")
        elif var in ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']:
            print(f"🔐 {var} = [your-google-oauth-credentials]")
        elif var in ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']:
            print(f"📧 {var} = [your-gmail-credentials]")
        else:
            # Show actual values for non-sensitive vars
            local_value = os.getenv(var, '[NOT SET]')
            if '[NOT SET]' not in str(local_value):
                print(f"✅ {var} = {local_value}")
            else:
                print(f"❌ {var} = [NEEDS TO BE SET]")
    
    print(f"\n🎯 CRITICAL: Make sure ALL variables above are set in Railway!")
    print(f"📍 Railway Dashboard → Your Service → Variables tab")

if __name__ == "__main__":
    check_railway_env()