"""Quick fix for passwords using bcrypt"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, bcrypt
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Use raw SQL for faster updates
    print("Updating all passwords to use bcrypt...")
    
    # Get all users
    users = User.query.all()
    total = len(users)
    
    print(f"Found {total} users to update")
    
    for idx, user in enumerate(users, 1):
        if user.username == 'admin':
            password = 'admin123'
        else:
            password = f"{user.username}emp@123"
        
        # Generate bcrypt hash
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Update user
        user.password_hash = password_hash
        user.is_active = True
        
        if idx % 50 == 0 or idx == total:
            db.session.commit()
            print(f"  Updated {idx}/{total} users...")
    
    print(f"\n✅ All {total} passwords updated with bcrypt!")
    print("✅ is_active set to True for all users")
    print("\n📋 Try logging in:")
    print("   Admin: admin / admin123")
    print("   Employee: 1009 / 1009emp@123")
