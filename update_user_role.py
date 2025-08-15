#!/usr/bin/env python3
"""
Update User Role Script
Quick script to promote a user to admin role
"""

import os
from dotenv import load_dotenv
from models_postgresql_optimized import db, User, init_db
from flask import Flask

# Load environment
load_dotenv()

# Create Flask app for database context
app = Flask(__name__)
database_url = os.getenv('DATABASE_URL')
if not database_url:
    database_url = 'postgresql://username:password@localhost/metabolomics_db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = init_db(app)

def update_user_role():
    """Update user role to admin"""
    with app.app_context():
        try:
            # Get all users
            users = User.query.all()
            
            if not users:
                print("❌ No users found in database")
                return
            
            print("📋 Current users in database:")
            for i, user in enumerate(users, 1):
                print(f"   {i}. {user.email} - Role: {user.role} - Name: {user.full_name}")
            
            if len(users) == 1:
                # Auto-select if only one user
                user_to_update = users[0]
                print(f"\n🎯 Auto-selecting only user: {user_to_update.email}")
            else:
                # Let user choose
                while True:
                    try:
                        choice = int(input(f"\n🎯 Select user to promote to admin (1-{len(users)}): ")) - 1
                        if 0 <= choice < len(users):
                            user_to_update = users[choice]
                            break
                        else:
                            print(f"❌ Please enter a number between 1 and {len(users)}")
                    except ValueError:
                        print("❌ Please enter a valid number")
            
            # Confirm the update
            print(f"\n📝 About to promote user:")
            print(f"   Email: {user_to_update.email}")
            print(f"   Name: {user_to_update.full_name}")
            print(f"   Current Role: {user_to_update.role}")
            print(f"   New Role: admin")
            
            confirm = input("\n✅ Confirm promotion? (y/N): ").lower().strip()
            
            if confirm in ['y', 'yes']:
                # Update the role
                old_role = user_to_update.role
                user_to_update.role = 'admin'
                db.session.commit()
                
                print(f"\n🎉 SUCCESS! User {user_to_update.email} promoted from '{old_role}' to 'admin'")
                print("\n📋 Updated user info:")
                print(f"   Email: {user_to_update.email}")
                print(f"   Name: {user_to_update.full_name}")
                print(f"   Role: {user_to_update.role}")
                print(f"   Admin Access: {'✅ YES' if user_to_update.is_admin() else '❌ NO'}")
                print(f"   Manager Access: {'✅ YES' if user_to_update.is_manager() else '❌ NO'}")
                
                print("\n🚀 You can now access:")
                print("   • Admin Dashboard (/admin)")
                print("   • Database Management (/manage-lipids)")
                print("   • All platform features")
                
            else:
                print("\n❌ Operation cancelled")
                
        except Exception as e:
            print(f"❌ Error updating user role: {e}")
            db.session.rollback()

if __name__ == '__main__':
    print("🔐 Metabolomics Platform - User Role Update Tool")
    print("=" * 50)
    update_user_role()