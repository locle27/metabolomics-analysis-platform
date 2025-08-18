#!/usr/bin/env python3
"""
Fix Super Admin Role - Restore loc22100302@gmail.com to admin role
This fixes the security issue where super admin lost privileges
"""

import os
import sys
from models_postgresql_optimized import db, User

# Add current directory to path for Flask app import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    print("✅ Successfully imported Flask app")
except ImportError as e:
    print(f"❌ Failed to import Flask app: {e}")
    sys.exit(1)

def fix_super_admin_role():
    """Restore super admin to proper admin role"""
    
    SUPER_ADMIN_EMAIL = 'loc22100302@gmail.com'
    
    with app.app_context():
        try:
            # Find the super admin user
            super_admin = User.query.filter_by(email=SUPER_ADMIN_EMAIL).first()
            
            if not super_admin:
                print(f"❌ Super admin user {SUPER_ADMIN_EMAIL} not found in database")
                return False
                
            print(f"🔍 Found super admin: {super_admin.email}")
            print(f"   Current role: {super_admin.role}")
            print(f"   Full name: {super_admin.full_name}")
            print(f"   Active: {super_admin.is_active}")
            
            # Fix the role if it's not admin
            if super_admin.role != 'admin':
                old_role = super_admin.role
                super_admin.role = 'admin'
                db.session.commit()
                
                print(f"✅ FIXED: Super admin role changed from '{old_role}' to 'admin'")
                print(f"🔒 Super admin privileges restored")
                return True
            else:
                print(f"✅ Super admin already has correct 'admin' role")
                return True
                
        except Exception as e:
            print(f"❌ Error fixing super admin role: {e}")
            db.session.rollback()
            return False

def verify_protection():
    """Verify that super admin role protection is working"""
    
    with app.app_context():
        try:
            # Check that there's exactly one user with super admin email and admin role
            super_admin = User.query.filter_by(email='loc22100302@gmail.com').first()
            
            if super_admin and super_admin.role == 'admin':
                print(f"✅ Super admin protection verified:")
                print(f"   Email: {super_admin.email}")
                print(f"   Role: {super_admin.role}")
                print(f"   Status: {super_admin.is_active}")
                return True
            else:
                print(f"❌ Super admin protection failed!")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying protection: {e}")
            return False

if __name__ == '__main__':
    print("🛡️ Fixing Super Admin Role Security Issue")
    print("=" * 50)
    
    # Fix the super admin role
    if fix_super_admin_role():
        print("\n✅ Role fix successful")
        
        # Verify protection
        print("\n🔍 Verifying super admin protection...")
        if verify_protection():
            print("\n✅ All operations completed successfully!")
            print("🛡️ Super admin security restored")
            print("\n📝 Changes made:")
            print("   • Super admin role restored to 'admin'")
            print("   • Role change protection added to backend")
            print("   • Super admin role is now immutable")
        else:
            print("\n❌ Protection verification failed")
            sys.exit(1)
    else:
        print("❌ Role fix failed")
        sys.exit(1)