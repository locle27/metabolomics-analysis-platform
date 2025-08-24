#!/bin/bash

# Database Setup Script for Metabolomics Platform
# Installs dependencies and initializes database

echo "🚀 Metabolomics Platform - Database Setup"
echo "======================================="

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: Not in a virtual environment!"
    echo "💡 It's recommended to use a virtual environment:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate  # Linux/Mac"
    echo "   venv\\Scripts\\activate     # Windows"
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled"
        exit 1
    fi
fi

# Step 1: Install required packages
echo "📦 Installing required packages..."
pip install psycopg2-binary Flask-SQLAlchemy

if [ $? -ne 0 ]; then
    echo "❌ Failed to install packages"
    echo "💡 Try: pip install psycopg2-binary==2.9.7"
    exit 1
fi

echo "✅ Packages installed successfully"

# Step 2: Initialize database
echo ""
echo "🗄️ Initializing database..."
python init_database.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Database setup completed successfully!"
    echo ""
    echo "🎯 You can now login with these demo accounts:"
    echo "   👑 Admin:   admin@demo.com / admin123"
    echo "   🛠️  Manager: manager@demo.com / manager123"
    echo "   👤 User:    user@demo.com / user123"
    echo ""
    echo "🚀 Start the application with: python app.py"
else
    echo ""
    echo "❌ Database initialization failed!"
    echo "💡 Check the error messages above for troubleshooting"
fi