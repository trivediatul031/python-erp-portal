"""
Fix employee passwords by regenerating hashes using Flask-Bcrypt
This ensures all passwords are properly hashed and will work with the login system
"""

import sys
from app import create_app, db
from app.models import User
from flask_bcrypt import Bcrypt

app = create_app()
bcrypt = Bcrypt(app)

def fix_passwords():
    with app.app_context():
        # The password we want to set for all employees
        password = 'admin123'
        
        # Generate a fresh hash
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        print(f"Generated new password hash: {password_hash}\n")
        
        # Get all employee users
        employees = User.query.filter_by(role='employee').all()
        
        if not employees:
            print("No employee users found in database!")
            return
        
        print(f"Found {len(employees)} employee users:\n")
        
        # Update each employee
        for user in employees:
            old_hash = user.password_hash
            user.password_hash = password_hash
            print(f"  {user.username} (ID: {user.user_id})")
            print(f"    Old hash: {old_hash[:50]}...")
            print(f"    New hash: {password_hash[:50]}...")
            
        # Commit all changes
        db.session.commit()
        print(f"\n✓ Updated {len(employees)} employee passwords")
        
        # Verify the changes
        print("\nVerifying passwords...")
        for user in User.query.filter_by(role='employee').all():
            if bcrypt.check_password_hash(user.password_hash, password):
                print(f"  ✓ {user.username}: Password verification PASSED")
            else:
                print(f"  ✗ {user.username}: Password verification FAILED")
        
        # Also show admin for comparison
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("\nAdmin verification:")
            if bcrypt.check_password_hash(admin.password_hash, password):
                print(f"  ✓ admin: Password verification PASSED")
            else:
                print(f"  ✗ admin: Password verification FAILED")

if __name__ == '__main__':
    try:
        fix_passwords()
        print("\n✓ All done! You can now login with:")
        print("  Username: robertk (or employee1, john.doe)")
        print("  Password: admin123")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
