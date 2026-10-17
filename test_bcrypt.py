"""Test bcrypt hashing"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, bcrypt

app = create_app()

with app.app_context():
    # Test admin user
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print(f"Admin found: {admin.username}")
        
        # Test password
        test_pass = 'admin123'
        print(f"Testing password: {test_pass}")
        
        # Generate new hash
        try:
            new_hash = bcrypt.generate_password_hash(test_pass).decode('utf-8')
            print(f"Generated hash: {new_hash[:50]}...")
            
            # Update admin
            admin.password_hash = new_hash
            admin.is_active = True
            db.session.commit()
            print("✅ Admin password updated!")
            
            # Test check
            if admin.check_password(test_pass):
                print("✅ Password check works!")
            else:
                print("❌ Password check failed!")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Admin not found")
