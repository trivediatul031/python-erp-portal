"""Fix admin account - set correct username and is_active"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Find admin user (case insensitive)
    admin = User.query.filter(User.username.ilike('admin')).first()
    
    admin_password = 'admin123'
    
    if admin:
        print(f"Found admin user: {admin.username}")
        
        # Update admin account
        admin.username = 'admin'  # Lowercase
        admin.password_hash = generate_password_hash(admin_password)
        admin.role = 'admin'
        admin.is_active = True  # Set to True
        admin.emp_id = None  # Admin doesn't need emp_id
        
        db.session.commit()
        print(f"✅ Updated admin account")
    else:
        # Create new admin
        admin = User(
            username='admin',
            password_hash=generate_password_hash(admin_password),
            emp_id=None,
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Created new admin account")
    
    print(f"\n📋 Admin Login Credentials:")
    print(f"   Username: admin")
    print(f"   Password: {admin_password}")
    print(f"   Is Active: True")
    print(f"\n✅ Admin login ready! Try logging in now.")
