"""
Simple script to fix employee passwords
"""

import sys
from app import create_app, db
from app.models import User
from flask_bcrypt import Bcrypt

app = create_app()
bcrypt = Bcrypt(app)

def fix_passwords():
    with app.app_context():
        password = 'admin123'
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        print(f"Generated new hash: {password_hash[:50]}...\n")
        
        # Update all employees
        result = db.session.execute(
            db.text("UPDATE users SET password_hash = :hash WHERE role = 'employee'"),
            {"hash": password_hash}
        )
        db.session.commit()
        
        affected = result.rowcount
        print(f"✓ Updated {affected} employee users\n")
        
        # Quick test
        user = User.query.filter_by(username='john.doe').first()
        if user:
            test = bcrypt.check_password_hash(user.password_hash, password)
            print(f"Test login for john.doe: {'✓ PASS' if test else '✗ FAIL'}")
        
        admin = User.query.filter_by(username='admin').first()
        if admin:
            test = bcrypt.check_password_hash(admin.password_hash, password)
            print(f"Test login for admin: {'✓ PASS' if test else '✗ FAIL'}")
        
        print("\n✓ Done! Try logging in with:")
        print("  Username: john.doe")
        print("  Password: admin123")

if __name__ == '__main__':
    try:
        fix_passwords()
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
