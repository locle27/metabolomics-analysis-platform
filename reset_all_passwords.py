#!/usr/bin/env python3
"""
Reset all user passwords to '1' for Railway free tier migration
This removes OAuth dependency and allows local username/password login
"""

from app import app, db
from models import User
from datetime import datetime

def reset_all_passwords():
    """Reset all user passwords to '1'"""

    new_password = '1'

    with app.app_context():
        users = User.query.all()

        print("=" * 80)
        print("🔒 RESETTING ALL USER PASSWORDS")
        print("=" * 80)
        print(f"Total users: {len(users)}")
        print(f"New password: '{new_password}'")
        print()

        updated_count = 0

        for user in users:
            print(f"Updating: {user.username} ({user.email})")

            # Set password to '1'
            user.set_password(new_password)

            # Update auth method to password
            user.auth_method = 'password'

            # Mark as active
            user.is_active = True

            # Clear any account locks
            user.locked_until = None
            user.failed_login_attempts = 0

            print(f"  ✅ Password reset to '{new_password}'")
            print(f"  ✅ Auth method: password")
            print(f"  ✅ Account active: True")
            print()

            updated_count += 1

        # Commit all changes
        db.session.commit()

        print("=" * 80)
        print(f"✅ PASSWORD RESET COMPLETE")
        print(f"   Users updated: {updated_count}")
        print(f"   New password for all users: '{new_password}'")
        print("=" * 80)
        print()
        print("Login credentials for all users:")
        print("-" * 80)

        users = User.query.all()
        for user in users:
            print(f"Username: {user.username:<30} Email: {user.email:<40} Password: {new_password}")

        print("-" * 80)
        print()
        print("🔑 All users can now login with:")
        print(f"   - Their username or email")
        print(f"   - Password: '{new_password}'")
        print()

if __name__ == '__main__':
    reset_all_passwords()
