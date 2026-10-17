"""
Create employee users with proper password hashes
"""

from app import create_app, db
from app.models import User, Employee
from datetime import datetime

app = create_app()

def create_users():
    with app.app_context():
        # Check existing employees in database
        employees = Employee.query.all()
        print(f"Found {len(employees)} employees in database:\n")
        
        for emp in employees:
            print(f"  {emp.emp_id}: {emp.name} ({emp.email})")
            
            # Check if user exists
            user = User.query.filter_by(emp_id=emp.emp_id).first()
            
            if user:
                print(f"    → User exists: {user.username}")
                # Update password
                user.set_password('admin123')
                print(f"    → Password updated")
            else:
                # Create new user
                username = emp.email.split('@')[0].replace('.', '_')
                new_user = User(
                    username=username,
                    role='employee',
                    emp_id=emp.emp_id,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                new_user.set_password('admin123')
                db.session.add(new_user)
                print(f"    → Created user: {username}")
            
            print()
        
        # Commit all changes
        db.session.commit()
        print("✓ All employee users created/updated!")
        
        # Show all users
        print("\nAll users in system:")
        all_users = User.query.all()
        for u in all_users:
            print(f"  Username: {u.username:15} Role: {u.role:10} Emp ID: {u.emp_id}")
        
        print("\n✓ Done! Login credentials:")
        print("  Password: admin123 (for all users)")

if __name__ == '__main__':
    try:
        create_users()
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
