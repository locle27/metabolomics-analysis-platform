#!/usr/bin/env python3
"""
Database connectivity test for Railway
Tests if the issue is database connection or other imports
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def health_check():
    """Health check with database connection test"""
    result = {
        "status": "healthy",
        "message": "Database test app running",
        "environment": os.getenv('FLASK_ENV', 'development'),
        "database_url_present": bool(os.getenv('DATABASE_URL')),
        "tests": {}
    }
    
    # Test 1: Basic environment variables
    result["tests"]["env_vars"] = {
        "DATABASE_URL": "✅ Present" if os.getenv('DATABASE_URL') else "❌ Missing",
        "SECRET_KEY": "✅ Present" if os.getenv('SECRET_KEY') else "❌ Missing",
        "FLASK_ENV": os.getenv('FLASK_ENV', 'Not set')
    }
    
    # Test 2: Try importing SQLAlchemy
    try:
        from flask_sqlalchemy import SQLAlchemy
        result["tests"]["sqlalchemy_import"] = "✅ Success"
    except Exception as e:
        result["tests"]["sqlalchemy_import"] = f"❌ Failed: {str(e)}"
        return jsonify(result), 500
    
    # Test 3: Try database connection
    try:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy()
        db.init_app(app)
        
        with app.app_context():
            # Try a simple query
            db.engine.execute("SELECT 1").fetchone()
            result["tests"]["database_connection"] = "✅ Success"
            
    except Exception as e:
        result["tests"]["database_connection"] = f"❌ Failed: {str(e)}"
        # Don't fail the health check for database issues
    
    return jsonify(result)

@app.route('/simple')
def simple_check():
    """Ultra simple check with no database"""
    return {"status": "ok", "message": "Simple check works"}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🧪 Starting DATABASE test app on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)