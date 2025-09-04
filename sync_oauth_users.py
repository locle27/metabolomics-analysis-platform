#!/usr/bin/env python3
"""
Sync OAuth Users Full Names
Migration script to identify and update OAuth users who may have incomplete full names
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def sync_oauth_users():
    """Identify OAuth users and their current full_name status"""
    try:
        # Import after setting path
        from app import app, db
        from models import User
        
        with app.app_context():
            print("🔍 OAUTH USERS ANALYSIS")
            print("=" * 50)
            
            # Find all OAuth users
            oauth_users = User.query.filter_by(auth_method='oauth').all()
            print(f"📊 Total OAuth users found: {len(oauth_users)}")
            
            if len(oauth_users) == 0:
                print("✅ No OAuth users found - nothing to sync")
                return
                
            print("\n📋 OAuth Users Status:")
            print("-" * 80)
            
            needs_sync = []
            already_synced = []
            
            for user in oauth_users:
                # Check full_name status
                has_full_name = bool(user.full_name and user.full_name.strip())
                is_email_username = False
                
                if has_full_name:
                    # Check if full_name looks like it's just the email username
                    email_prefix = user.email.split('@')[0] if user.email else ''
                    is_email_username = user.full_name.strip().lower() == email_prefix.lower()
                
                status = "✅ HAS FULL NAME"
                if not has_full_name:
                    status = "❌ MISSING FULL NAME"
                    needs_sync.append(user)
                elif is_email_username:
                    status = "⚠️ USING EMAIL USERNAME"
                    needs_sync.append(user)
                else:
                    already_synced.append(user)
                
                print(f"👤 {user.email:<35} | {status:<20} | '{user.full_name or 'NULL'}'")
            
            print(f"\n📈 SUMMARY:")
            print(f"   ✅ Already synced: {len(already_synced)}")
            print(f"   ⚠️ Need sync: {len(needs_sync)}")
            
            if needs_sync:
                print(f"\n🔧 USERS NEEDING SYNC:")
                for user in needs_sync:
                    print(f"   • {user.email} - {user.full_name or 'No full name'}")
                
                print(f"\n💡 NEXT STEPS:")
                print(f"   1. These users will auto-sync when they next log in with Google")
                print(f"   2. Or use the admin sync option to prompt re-authentication")
                print(f"   3. Manual update option available for immediate sync")
                
                return needs_sync
            else:
                print(f"\n🎉 All OAuth users already have proper full names!")
                return []
                
    except Exception as e:
        print(f"❌ Error analyzing OAuth users: {e}")
        import traceback
        traceback.print_exc()
        return []

def manual_update_oauth_user(email, new_full_name):
    """Manually update a specific OAuth user's full name"""
    try:
        from app import app, db
        from models import User
        
        with app.app_context():
            user = User.query.filter_by(email=email, auth_method='oauth').first()
            if not user:
                print(f"❌ OAuth user {email} not found")
                return False
            
            old_name = user.full_name
            user.full_name = new_full_name
            db.session.commit()
            
            print(f"✅ Updated {email}:")
            print(f"   Old: '{old_name}'")
            print(f"   New: '{new_full_name}'")
            return True
            
    except Exception as e:
        print(f"❌ Error updating user {email}: {e}")
        return False

if __name__ == '__main__':
    print("🚀 OAUTH USERS FULL NAME SYNC TOOL")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'analyze':
            sync_oauth_users()
        elif sys.argv[1] == 'update' and len(sys.argv) >= 4:
            email = sys.argv[2]
            full_name = ' '.join(sys.argv[3:])
            manual_update_oauth_user(email, full_name)
        else:
            print("Usage:")
            print("  python3 sync_oauth_users.py analyze")
            print("  python3 sync_oauth_users.py update email@domain.com 'Full Name'")
    else:
        # Default: analyze
        sync_oauth_users()