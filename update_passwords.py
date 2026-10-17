"""
Update all employee passwords to the new format: [emp_code]emp@123
"""
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Employee
from werkzeug.security import generate_password_hash

def main():
    app = create_app()
    
    with app.app_context():
        # Get all employees
        employees = Employee.query.all()
        
        updated_count = 0
        created_count = 0
        
        for employee in employees:
            emp_id = employee.emp_id
            
            # Generate new password in format: [emp_id]emp@123
            new_password = f"{emp_id}emp@123"
            password_hash = generate_password_hash(new_password)
            
            # Check if user exists
            user = User.query.filter_by(emp_id=emp_id).first()
            
            if user:
                # Update existing user password
                user.password_hash = password_hash
                user.username = emp_id  # Ensure username is set correctly
                updated_count += 1
                print(f"Updated: {emp_id} - Username: {emp_id}, Password: {new_password}")
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
                print(f"Created: {emp_id} - Username: {emp_id}, Password: {new_password}")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Success!")
            print(f"   - Updated {updated_count} existing users")
            print(f"   - Created {created_count} new users")
            print(f"   - Total: {updated_count + created_count} user accounts ready")
            print(f"\nPassword format: [emp_code]emp@123")
            print(f"Example: Employee 1009 → Username: 1009, Password: 1009emp@123")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()
