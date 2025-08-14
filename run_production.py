#!/usr/bin/env python3
"""
Production Server Runner (for local testing of production settings)
- Uses environment variables (not .env file)
- Production-like settings
- No debug mode
"""

import os

# Verify production environment
print("🚀 PRODUCTION MODE (Local Testing)")
print(f"📊 Database: {os.getenv('DATABASE_URL', 'NOT CONFIGURED')[:50]}...")
print(f"🔧 Flask Environment: {os.getenv('FLASK_ENV', 'production')}")
print(f"🐛 Debug Mode: {os.getenv('FLASK_DEBUG', 'False')}")
print("=" * 60)

# Import and run Flask app
if __name__ == '__main__':
    from app import app
    
    # Production server settings (local testing)
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=False,
        use_reloader=False
    )