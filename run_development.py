#!/usr/bin/env python3
"""
Development Server Runner
- Uses .env file for configuration
- Connects to Railway database for testing with production data
- Debug mode enabled
- Hot reload enabled
"""

import os
from dotenv import load_dotenv

# Load development environment
load_dotenv('.env')

# Verify environment
print("🧪 DEVELOPMENT MODE")
print(f"📊 Database: {os.getenv('DATABASE_URL', 'NOT CONFIGURED')[:50]}...")
print(f"🔧 Flask Environment: {os.getenv('FLASK_ENV', 'development')}")
print(f"🐛 Debug Mode: {os.getenv('FLASK_DEBUG', 'True')}")
print("=" * 60)

# Import and run Flask app
if __name__ == '__main__':
    from app import app
    
    # Development server settings
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=True,
        use_debugger=True
    )