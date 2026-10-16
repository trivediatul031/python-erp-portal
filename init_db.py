"""Initialize SQLite database with tables and default admin user"""
from app import create_app
from app.models import db, User, Employee
from datetime import datetime

app = create_app()

with app.app_context():
    # Drop all tables and recreate (for fresh start)
    print("Creating database tables...")
    db.drop_all()
    db.create_all()
    
    # Create default admin employee
    admin_employee = Employee(
        emp_id='ADMIN',
        name='System Administrator',
        email='admin@tas-erp.com',
        department='IT',
        designation='Administrator',
        is_active=True
    )
    db.session.add(admin_employee)
    db.session.commit()
    print("✓ Created admin employee record")
    
    # Create default admin user
    admin_user = User(
        username='admin',
        role='admin',
        emp_id='ADMIN',
        is_active=True
    )
    admin_user.set_password('admin123')
    db.session.add(admin_user)
    db.session.commit()
    print("✓ Created admin user (username: admin, password: admin123)")
    
    print("\n" + "="*50)
    print("Database initialized successfully!")
    print("="*50)
    print("\nYou can now run the application with:")
    print("  python run.py")
    print("\nLogin with:")
    print("  Username: admin")
    print("  Password: admin123")
    print("="*50)
