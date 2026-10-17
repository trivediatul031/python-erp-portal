"""Check admin account status"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from werkzeug.security import check_password_hash

app = create_app()

with app.app_context():
    # Find admin user
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print(f"✅ Admin user found:")
        print(f"   Username: {admin.username}")
        print(f"   Role: {admin.role}")
        print(f"   Emp ID: {admin.emp_id}")
        print(f"   Is Active: {admin.is_active}")
        print(f"   Has password hash: {bool(admin.password_hash)}")
        
        # Test password
        test_password = 'admin123'
        password_works = check_password_hash(admin.password_hash, test_password)
        print(f"   Password 'admin123' works: {password_works}")
        
        if not password_works:
            # Try checking the password with the check_password method
            try:
                password_works_method = admin.check_password(test_password)
                print(f"   Password via check_password(): {password_works_method}")
            except Exception as e:
                print(f"   Error checking password: {str(e)}")
    else:
        print("❌ Admin user not found!")
    
    # Count total users
    total_users = User.query.count()
    print(f"\n📊 Total users in database: {total_users}")
