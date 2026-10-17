"""
Fix employee codes and passwords - handles foreign key constraints
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Employee, TASRecord
from werkzeug.security import generate_password_hash
from sqlalchemy import text

def clean_emp_id(emp_id):
    """Remove .0 suffix from employee codes"""
    emp_id_str = str(emp_id)
    if '.' in emp_id_str and emp_id_str.replace('.', '').replace('-', '').isdigit():
        try:
            return str(int(float(emp_id_str)))
        except:
            return emp_id_str
    return emp_id_str

def main():
    app = create_app()
    
    with app.app_context():
        print("Starting fix process...\n")
        
        # Step 1: Delete all user accounts (they reference employees)
        print("Step 1: Removing existing user accounts...")
        users_deleted = User.query.delete()
        db.session.commit()
        print(f"✅ Deleted {users_deleted} user accounts\n")
        
        # Step 2: Update employee codes
        print("Step 2: Cleaning employee codes...")
        employees = Employee.query.all()
        
        updates = []
        for employee in employees:
            old_emp_id = employee.emp_id
            new_emp_id = clean_emp_id(old_emp_id)
            
            if old_emp_id != new_emp_id:
                updates.append((employee, old_emp_id, new_emp_id))
                print(f"  {old_emp_id} → {new_emp_id}")
        
        # Disable foreign key checks temporarily
        db.session.execute(text('SET FOREIGN_KEY_CHECKS=0'))
        
        # Update employee codes
        for employee, old_id, new_id in updates:
            # Update TAS records first
            db.session.execute(
                text('UPDATE tas_records SET emp_id = :new_id WHERE emp_id = :old_id'),
                {'new_id': new_id, 'old_id': old_id}
            )
            # Update manager references
            db.session.execute(
                text('UPDATE employees SET manager_id = :new_id WHERE manager_id = :old_id'),
                {'new_id': new_id, 'old_id': old_id}
            )
            # Update employee code
            employee.emp_id = new_id
        
        db.session.commit()
        
        # Re-enable foreign key checks
        db.session.execute(text('SET FOREIGN_KEY_CHECKS=1'))
        db.session.commit()
        
        print(f"✅ Updated {len(updates)} employee codes\n")
        
        # Step 3: Create new user accounts with clean codes and passwords
        print("Step 3: Creating user accounts with new passwords...")
        
        employees = Employee.query.all()
        created_count = 0
        
        for employee in employees:
            emp_id = employee.emp_id
            
            # Generate password: [emp_id]emp@123
            password = f"{emp_id}emp@123"
            password_hash = generate_password_hash(password)
            
            # Create user
            new_user = User(
                username=emp_id,
                password_hash=password_hash,
                emp_id=emp_id,
                role='employee'
            )
            db.session.add(new_user)
            created_count += 1
            print(f"  Created: Username={emp_id}, Password={password}")
        
        db.session.commit()
        
        print(f"\n✅ Success!")
        print(f"   - Fixed {len(updates)} employee codes (removed .0)")
        print(f"   - Created {created_count} user accounts")
        print(f"\n📋 Login Instructions:")
        print(f"   Username: Employee Code (e.g., 1009)")
        print(f"   Password: [code]emp@123 (e.g., 1009emp@123)")
        print(f"\n✅ All employees can now login!")

if __name__ == '__main__':
    main()
