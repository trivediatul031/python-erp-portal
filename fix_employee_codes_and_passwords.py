"""
Fix employee codes (remove .0) and update passwords to new format
"""
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Employee
from werkzeug.security import generate_password_hash

def clean_emp_id(emp_id):
    """Remove .0 suffix from employee codes"""
    emp_id_str = str(emp_id)
    # If it's a number like 1009.0, convert to 1009
    if '.' in emp_id_str and emp_id_str.replace('.', '').replace('-', '').isdigit():
        try:
            return str(int(float(emp_id_str)))
        except:
            return emp_id_str
    return emp_id_str

def main():
    app = create_app()
    
    with app.app_context():
        print("Step 1: Cleaning employee codes...")
        
        # Get all employees
        employees = Employee.query.all()
        emp_code_updates = []
        
        for employee in employees:
            old_emp_id = employee.emp_id
            new_emp_id = clean_emp_id(old_emp_id)
            
            if old_emp_id != new_emp_id:
                emp_code_updates.append((employee, old_emp_id, new_emp_id))
                print(f"  {old_emp_id} → {new_emp_id}")
        
        # Update employee codes
        for employee, old_id, new_id in emp_code_updates:
            employee.emp_id = new_id
        
        # Commit employee code changes
        try:
            db.session.commit()
            print(f"✅ Updated {len(emp_code_updates)} employee codes\n")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating employee codes: {str(e)}\n")
            return
        
        print("Step 2: Updating user accounts and passwords...")
        
        # Refresh employees after commit
        employees = Employee.query.all()
        
        updated_count = 0
        created_count = 0
        deleted_count = 0
        
        # Delete old users with .0 codes
        old_users = User.query.filter(User.username.like('%.0')).all()
        for old_user in old_users:
            print(f"  Deleting old user: {old_user.username}")
            db.session.delete(old_user)
            deleted_count += 1
        
        db.session.commit()
        
        # Create/update users with clean codes
        for employee in employees:
            emp_id = employee.emp_id
            
            # Generate new password in format: [emp_id]emp@123
            new_password = f"{emp_id}emp@123"
            password_hash = generate_password_hash(new_password)
            
            # Check if user exists
            user = User.query.filter_by(username=emp_id).first()
            
            if user:
                # Update existing user password
                user.password_hash = password_hash
                user.emp_id = emp_id
                updated_count += 1
                print(f"  Updated: {emp_id} - Password: {new_password}")
            else:
                # Create new user
                new_user = User(
                    username=emp_id,
                    password_hash=password_hash,
                    emp_id=emp_id,
                    role='employee'
                )
                db.session.add(new_user)
                created_count += 1
                print(f"  Created: {emp_id} - Password: {new_password}")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Success!")
            print(f"   - Deleted {deleted_count} old user accounts")
            print(f"   - Updated {updated_count} existing users")
            print(f"   - Created {created_count} new users")
            print(f"   - Total: {updated_count + created_count} user accounts ready")
            print(f"\n📋 Login Format:")
            print(f"   Username: Employee Code (e.g., 1009)")
            print(f"   Password: [code]emp@123 (e.g., 1009emp@123)")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()
