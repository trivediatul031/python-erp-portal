"""
Fix admin login - ensure admin account exists with correct password
"""

from app import create_app, db
from app.models import User, Employee
from datetime import datetime

app = create_app()

with app.app_context():
    print("=" * 60)
    print("CHECKING ADMIN ACCOUNT")
    print("=" * 60)
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print(f"\n✓ Admin user found: {admin.username}")
        print(f"  Role: {admin.role}")
        print(f"  Active: {admin.is_active}")
        print(f"  Employee ID: {admin.emp_id}")
        
        # Reset password to admin123
        print("\nResetting admin password to: admin123")
        admin.set_password('admin123')
        admin.is_active = True
        db.session.commit()
        print("✓ Admin password reset successfully!")
        
        # Test the password
        if admin.check_password('admin123'):
            print("✓ Password verification: PASS")
        else:
            print("✗ Password verification: FAIL")
    else:
        print("\n✗ Admin user NOT found!")
        print("Creating new admin account...")
        
        # Check if ADMIN employee exists
        admin_emp = Employee.query.filter_by(emp_id='ADMIN').first()
        
        if not admin_emp:
            print("Creating ADMIN employee record...")
            admin_emp = Employee(
                emp_id='ADMIN',
                name='System Administrator',
                email='admin@test.com',
                department='IT',
                designation='Administrator',
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.session.add(admin_emp)
            db.session.flush()
            print(f"✓ Created employee: {admin_emp.name}")
        
        # Create admin user
        admin = User(
            username='admin',
            role='admin',
            emp_id='ADMIN',
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        print(f"✓ Created admin user: {admin.username}")
        print("✓ Password set to: admin123")
    
    print("\n" + "=" * 60)
    print("ADMIN LOGIN CREDENTIALS:")
    print("=" * 60)
    print("Username: admin")
    print("Password: admin123")
    print("=" * 60)
    print("\nYou can now login to the admin dashboard!")
    print("URL: http://127.0.0.1:5000")
