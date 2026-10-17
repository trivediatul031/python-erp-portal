"""
Create/Reset admin account
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def main():
    app = create_app()
    
    with app.app_context():
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        
        admin_password = 'admin123'
        
        if admin:
            # Update existing admin
            admin.password_hash = generate_password_hash(admin_password)
            admin.role = 'admin'
            print(f"✅ Updated existing admin account")
        else:
            # Create new admin
            admin = User(
                username='admin',
                password_hash=generate_password_hash(admin_password),
                emp_id=None,  # Admin doesn't need emp_id
                role='admin'
            )
            db.session.add(admin)
            print(f"✅ Created new admin account")
        
        db.session.commit()
        
        print(f"\n📋 Admin Login Credentials:")
        print(f"   Username: admin")
        print(f"   Password: {admin_password}")
        print(f"\n✅ Admin account is ready!")

if __name__ == '__main__':
    main()
