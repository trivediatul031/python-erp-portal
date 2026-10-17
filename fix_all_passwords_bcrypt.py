"""
Fix all passwords to use bcrypt (not werkzeug)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Employee, bcrypt

def main():
    app = create_app()
    
    with app.app_context():
        print("Fixing all user passwords to use bcrypt...\n")
        
        # Fix admin account
        admin = User.query.filter_by(username='admin').first()
        if admin:
            admin_password = 'admin123'
            admin.password_hash = bcrypt.generate_password_hash(admin_password).decode('utf-8')
            admin.is_active = True
            admin.role = 'admin'
            admin.emp_id = None
            print(f"✅ Fixed admin - Username: admin, Password: {admin_password}")
        else:
            # Create admin if doesn't exist
            admin_password = 'admin123'
            admin = User(
                username='admin',
                password_hash=bcrypt.generate_password_hash(admin_password).decode('utf-8'),
                role='admin',
                emp_id=None,
                is_active=True
            )
            db.session.add(admin)
            print(f"✅ Created admin - Username: admin, Password: {admin_password}")
        
        db.session.commit()
        
        # Fix all employee accounts
        employees = Employee.query.all()
        fixed_count = 0
        
        for employee in employees:
            emp_id = employee.emp_id
            
            # Find or create user
            user = User.query.filter_by(username=emp_id).first()
            
            # Generate password: [emp_id]emp@123
            password = f"{emp_id}emp@123"
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            
            if user:
                # Update existing
                user.password_hash = password_hash
                user.is_active = True
                user.emp_id = emp_id
                user.role = 'employee'
            else:
                # Create new
                user = User(
                    username=emp_id,
                    password_hash=password_hash,
                    emp_id=emp_id,
                    role='employee',
                    is_active=True
                )
                db.session.add(user)
            
            fixed_count += 1
            if fixed_count % 50 == 0:
                print(f"  Progress: {fixed_count}/{len(employees)} employees...")
        
        db.session.commit()
        
        print(f"\n✅ Success!")
        print(f"   - Fixed admin account")
        print(f"   - Fixed {fixed_count} employee accounts")
        print(f"\n📋 Login Credentials:")
        print(f"   Admin: username=admin, password=admin123")
        print(f"   Employees: username=[emp_code], password=[emp_code]emp@123")
        print(f"\n🔐 All passwords now use bcrypt hashing")
        print(f"✅ Login should work now!")

if __name__ == '__main__':
    main()
