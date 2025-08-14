#!/bin/bash

# Metabolomics Project Backup Restoration Script
# Usage: ./restore_backup.sh [backup_date]

echo "🔄 METABOLOMICS PROJECT BACKUP RESTORATION"
echo "=========================================="

# Show available backups
echo "📁 Available backups:"
ls -la backups/backup_*_metabolomics_fast.db 2>/dev/null | tail -5
echo ""

# Get latest backup if no date specified
if [ -z "$1" ]; then
    LATEST_DB=$(ls -t backups/backup_*_metabolomics_fast.db 2>/dev/null | head -1)
    if [ -z "$LATEST_DB" ]; then
        echo "❌ No database backups found!"
        exit 1
    fi
    echo "🎯 Using latest backup: $LATEST_DB"
else
    LATEST_DB="backups/backup_${1}_metabolomics_fast.db"
    if [ ! -f "$LATEST_DB" ]; then
        echo "❌ Backup not found: $LATEST_DB"
        exit 1
    fi
    echo "🎯 Using specified backup: $LATEST_DB"
fi

# Create restoration backup of current state
echo "💾 Backing up current state before restoration..."
cp metabolomics_fast.db "backups/pre_restore_$(date +%Y%m%d_%H%M%S)_metabolomics_fast.db" 2>/dev/null

# Restore database
echo "🔄 Restoring database..."
cp "$LATEST_DB" metabolomics_fast.db

# Restore Python files if available
LATEST_PYTHON=$(ls -t backups/python_files_*.tar.gz 2>/dev/null | head -1)
if [ -n "$LATEST_PYTHON" ]; then
    echo "🔄 Restoring Python files from: $LATEST_PYTHON"
    read -p "⚠️  This will overwrite current Python files. Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        tar -xzf "$LATEST_PYTHON"
        echo "✅ Python files restored"
    else
        echo "⏭️  Skipped Python files restoration"
    fi
fi

# Restore templates/static if available
LATEST_TEMPLATES=$(ls -t backups/templates_static_*.tar.gz 2>/dev/null | head -1)
if [ -n "$LATEST_TEMPLATES" ]; then
    echo "🔄 Restoring templates/static from: $LATEST_TEMPLATES"
    read -p "⚠️  This will overwrite current templates/static. Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        tar -xzf "$LATEST_TEMPLATES"
        echo "✅ Templates/static restored"
    else
        echo "⏭️  Skipped templates/static restoration"
    fi
fi

# Test restoration
echo "🧪 Testing restored database..."
python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('metabolomics_fast.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM main_lipids')
    count = cursor.fetchone()[0]
    print(f'✅ Database test successful: {count} lipids found')
    conn.close()
except Exception as e:
    print(f'❌ Database test failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 RESTORATION COMPLETED SUCCESSFULLY!"
    echo "✅ Database restored and tested"
    echo "🚀 You can now run: python app.py"
else
    echo ""
    echo "❌ RESTORATION FAILED!"
    echo "🔄 Restoring original database..."
    cp "backups/pre_restore_$(date +%Y%m%d)_"*"_metabolomics_fast.db" metabolomics_fast.db 2>/dev/null
    echo "💡 Check backup files manually in backups/ directory"
fi

echo ""
echo "📊 Current backup inventory:"
ls -la backups/ | grep -E "\.(db|tar\.gz)$"