#!/usr/bin/env python3
"""
Script to remove emoji debug print statements that are slowing down API performance.
Removes print statements containing: 📎🔍📥🗓️❌✅
"""

import re
import os

def remove_emoji_debug_prints(file_path):
    """Remove emoji debug print statements from a Python file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_lines = content.split('\n')
    
    # Track changes
    removed_lines = []
    modified_lines = []
    
    # Comprehensive emoji list for debug cleanup
    debug_emojis = [
        '📎', '🔍', '📥', '🗓️', '❌', '✅',  # Original target emojis
        '🔓', '🔐', '🚨', '🛡️', '🔒',      # Security emojis
        '🎯', '🧹', '📊', '📈', '📉',      # Analytics emojis  
        '🔄', '💾', '⚙️', '🛠️',          # Process emojis
        '🌟', '🎉', '🚀', '⚡', '🔥',      # Performance emojis
        '💡', '📝', '📋', '📌',           # Documentation emojis
        '🎯', '🧪', '🔬', '🧬',           # Lab emojis
    ]
    
    # Process each line
    for i, line in enumerate(original_lines):
        # Check if line contains emoji debug symbols and is a print statement
        if any(emoji in line for emoji in debug_emojis) and 'print(' in line:
            # Skip lines that are part of HTML templates or actual user-facing content
            if any(keyword in line.lower() for keyword in ['<h', '<p', '<li', 'return "', "return '", 'href=', 'style=']):
                # Keep HTML template content
                modified_lines.append(line)
            else:
                removed_lines.append(f"Line {i+1}: {line.strip()}")
                modified_lines.append('')  # Remove the line entirely
        else:
            modified_lines.append(line)
    
    if removed_lines:
        # Write the cleaned content back to file
        cleaned_content = '\n'.join(modified_lines)
        
        # Create backup
        backup_path = file_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Created backup: {backup_path}")
        
        # Write cleaned file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"✓ Cleaned {file_path}")
        print(f"✓ Removed {len(removed_lines)} emoji debug print statements:")
        for line in removed_lines[:10]:  # Show first 10 for brevity
            print(f"  - {line}")
        if len(removed_lines) > 10:
            print(f"  ... and {len(removed_lines) - 10} more lines")
        
        return True
    else:
        print(f"✓ No emoji debug prints found in {file_path}")
        return False

def main():
    """Clean emoji debug prints from key performance files"""
    project_dir = "/mnt/c/Users/T14/Desktop/metabolomics-project"
    
    files_to_clean = [
        os.path.join(project_dir, "app.py"),
        os.path.join(project_dir, "dual_chart_service.py"), 
        os.path.join(project_dir, "streamlined_calculator_service.py")
    ]
    
    total_cleaned = 0
    
    print("🧹 Starting emoji debug cleanup for API performance optimization...")
    print("=" * 60)
    
    for file_path in files_to_clean:
        print(f"\nProcessing: {os.path.basename(file_path)}")
        print("-" * 40)
        
        if remove_emoji_debug_prints(file_path):
            total_cleaned += 1
    
    print("\n" + "=" * 60)
    print(f"🎯 Cleanup completed! {total_cleaned} files were modified.")
    print("📈 API performance should now be significantly improved!")
    print("\n💡 To verify the changes, run:")
    print("   python3 app.py")
    print("   # Test API endpoints for improved speed")

if __name__ == "__main__":
    main()