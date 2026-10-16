"""Create an employee user account for testing"""
from app import create_app
from app.models import db, User, Employee

app = create_app()

with app.app_context():
    # Check if employee 1987 exists
    employee = Employee.query.get('1987')
    
    if not employee:
        print("⚠️  Employee 1987 not found!")
        print("Please import sample_employees.csv first")
        print("Or the employee needs to be added to the database")
    else:
        # Check if user already exists
        existing_user = User.query.filter_by(username='john.doe').first()
        
        if existing_user:
            print("⚠️  User 'john.doe' already exists!")
        else:
            # Create user for employee 1987 (John Doe from sample data)
            user = User(
                username='john.doe',
                role='employee',
                emp_id='1987',
                is_active=True
            )
            user.set_password('test123')
            db.session.add(user)
            db.session.commit()
            
            print("="*50)
            print("✓ Employee user created successfully!")
            print("="*50)
            print(f"Username: john.doe")
            print(f"Password: test123")
            print(f"Employee ID: 1987")
            print(f"Employee Name: {employee.name}")
            print("="*50)
            print("\nYou can now login as this employee to test TAS submission!")
