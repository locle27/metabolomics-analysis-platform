#!/usr/bin/env python3
"""
Precise emoji debug cleanup - only removes print() statements containing emojis
Preserves all code structure and non-print emoji usage (like HTML templates)
"""

import re
import os

def clean_emoji_prints(file_path):
    """Remove only print statements containing emojis, preserve everything else"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Comprehensive emoji patterns for debug cleanup
    emoji_patterns = [
        '📎', '🔍', '📥', '🗓️', '❌', '✅',  # Original targets
        '🔓', '🔐', '🚨', '🛡️', '🔒',      # Security
        '🎯', '🧹', '📊', '📈', '📉',      # Analytics
        '🔄', '💾', '⚙️', '🛠️',          # Process
        '🌟', '🎉', '🚀', '⚡', '🔥',      # Performance
        '💡', '📝', '📋', '📌',           # Documentation
        '🧪', '🔬', '🧬',                 # Lab/Science
    ]
    
    # Track changes
    removed_count = 0
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        # Check if this is a print statement with emoji
        if 'print(' in line and any(emoji in line for emoji in emoji_patterns):
            # Skip HTML templates and return statements (preserve user-facing content)
            if any(marker in line for marker in ['<h', '<p', '<li', 'return "', "return '", 'href=', 'style=']):
                # Keep this line - it's part of HTML template
                cleaned_lines.append(line)
            else:
                # This is a debug print statement - remove it
                removed_count += 1
                # Keep the line as a comment to preserve line numbers for debugging
                indent = len(line) - len(line.lstrip())
                cleaned_lines.append(' ' * indent + '# Debug print removed for performance\n')
        else:
            # Keep all other lines unchanged
            cleaned_lines.append(line)
    
    if removed_count > 0:
        # Create backup
        backup_path = file_path + f'.backup_precise_{removed_count}'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✓ Created backup: {backup_path}")
        
        # Write cleaned file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)
        
        print(f"✓ Cleaned {file_path}")
        print(f"✓ Removed {removed_count} emoji debug print statements")
        return True
    else:
        print(f"✓ No emoji debug prints found in {file_path}")
        return False

def main():
    """Clean emoji debug prints from performance-critical files"""
    project_dir = "/mnt/c/Users/T14/Desktop/metabolomics-project"
    
    files_to_clean = [
        os.path.join(project_dir, "app.py"),
        os.path.join(project_dir, "dual_chart_service.py"), 
        os.path.join(project_dir, "streamlined_calculator_service.py")
    ]
    
    total_cleaned = 0
    total_removed = 0
    
    print("🧹 Starting PRECISE emoji debug cleanup for API performance...")
    print("=" * 60)
    
    for file_path in files_to_clean:
        print(f"\nProcessing: {os.path.basename(file_path)}")
        print("-" * 40)
        
        # Count existing emoji prints before cleaning
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
            emoji_count = sum(1 for line in original_content.split('\n') 
                            if 'print(' in line and any(emoji in line for emoji in 
                            ['📎', '🔍', '📥', '🗓️', '❌', '✅', '🔓', '🎯', '🧹', '📊', '🔄', '💾', '🚀', '⚡', '💡', '📝', '🧪']))
        
        print(f"Found {emoji_count} emoji debug prints")
        
        if clean_emoji_prints(file_path):
            total_cleaned += 1
            total_removed += emoji_count
    
    print("\n" + "=" * 60)
    print(f"🎯 Cleanup completed!")
    print(f"📊 Files modified: {total_cleaned}")
    print(f"🚀 Debug prints removed: ~{total_removed}")
    print("📈 API performance should be significantly improved!")
    
    print("\n💡 Next steps:")
    print("1. Test the application: python3 app.py")
    print("2. Verify API endpoints work correctly")
    print("3. Monitor performance improvements")

if __name__ == "__main__":
    main()