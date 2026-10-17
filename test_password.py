"""Test password verification for users"""
from app import create_app
from app.models import User

app = create_app()

with app.app_context():
    print("="*60)
    print("Testing Password Verification")
    print("="*60)
    
    # Get all users
    users = User.query.all()
    
    print(f"\nFound {len(users)} users in database:\n")
    
    for user in users:
        print(f"Username: {user.username}")
        print(f"Role: {user.role}")
        print(f"Active: {user.is_active}")
        print(f"Password Hash: {user.password_hash[:50]}...")
        
        # Test with admin123
        test_password = "admin123"
        result = user.check_password(test_password)
        print(f"Password check ('{test_password}'): {'✓ PASS' if result else '✗ FAIL'}")
        print("-"*60)
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)
