#!/usr/bin/env python3
"""
Safe emoji debug cleanup - comments out print statements instead of removing them
This preserves code structure while improving performance
"""

import os

def comment_out_emoji_prints(file_path):
    """Comment out print statements containing emojis"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Emoji patterns to target
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
    commented_count = 0
    modified_lines = []
    
    for i, line in enumerate(lines):
        # Check if this is a print statement with emoji
        if 'print(' in line and any(emoji in line for emoji in emoji_patterns):
            # Skip HTML templates and return statements (preserve user-facing content)
            if any(marker in line for marker in ['<h', '<p', '<li', 'return "', "return '", 'href=', 'style=']):
                # Keep this line - it's part of HTML template
                modified_lines.append(line)
            else:
                # This is a debug print statement - comment it out
                commented_count += 1
                # Preserve indentation and add comment
                indent = line[:len(line) - len(line.lstrip())]
                modified_lines.append(f"{indent}# {line.strip()}  # Commented for performance\n")
        else:
            # Keep all other lines unchanged
            modified_lines.append(line)
    
    if commented_count > 0:
        # Create backup
        backup_path = file_path + f'.backup_safe_{commented_count}'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✓ Created backup: {backup_path}")
        
        # Write modified file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
        
        print(f"✓ Modified {file_path}")
        print(f"✓ Commented out {commented_count} emoji debug print statements")
        return True
    else:
        print(f"✓ No emoji debug prints found in {file_path}")
        return False

def main():
    """Comment out emoji debug prints from performance-critical files"""
    project_dir = "/mnt/c/Users/T14/Desktop/metabolomics-project"
    
    files_to_clean = [
        os.path.join(project_dir, "app.py"),
        os.path.join(project_dir, "dual_chart_service.py"), 
        os.path.join(project_dir, "streamlined_calculator_service.py")
    ]
    
    total_modified = 0
    total_commented = 0
    
    print("🧹 Starting SAFE emoji debug cleanup (commenting out prints)...")
    print("=" * 60)
    
    for file_path in files_to_clean:
        print(f"\nProcessing: {os.path.basename(file_path)}")
        print("-" * 40)
        
        if comment_out_emoji_prints(file_path):
            total_modified += 1
            # Count the actual number commented (rough estimate)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                commented = content.count('# Commented for performance')
                total_commented += commented
    
    print("\n" + "=" * 60)
    print(f"🎯 Safe cleanup completed!")
    print(f"📊 Files modified: {total_modified}")
    print(f"🚀 Debug prints commented out: {total_commented}")
    print("📈 API performance should be improved while preserving code structure!")
    
    print("\n💡 Testing application...")
    
    # Test import
    try:
        import sys
        sys.path.insert(0, project_dir)
        import app
        print("✅ Application import test: PASSED")
        print("🎯 Ready to test API performance!")
    except Exception as e:
        print(f"❌ Application import test failed: {e}")
        print("🔧 You may need to fix remaining issues manually")

if __name__ == "__main__":
    main()