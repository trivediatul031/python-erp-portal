"""Simple database setup - Run this once before starting the app"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    from app.models import db, User, Employee
    
    print("=" * 60)
    print("TAS ERP Portal - Database Setup")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        print("\n[1/4] Creating database tables...")
        db.create_all()
        print("✓ Tables created successfully!")
        
        print("\n[2/4] Creating admin employee record...")
        # Check if admin employee exists
        admin_emp = Employee.query.get('ADMIN')
        if not admin_emp:
            admin_emp = Employee(
                emp_id='ADMIN',
                name='System Administrator',
                email='admin@tas-erp.com',
                department='IT',
                designation='Administrator',
                is_active=True
            )
            db.session.add(admin_emp)
            db.session.commit()
            print("✓ Admin employee created!")
        else:
            print("✓ Admin employee already exists!")
        
        print("\n[3/4] Creating admin user account...")
        # Check if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                role='admin',
                emp_id='ADMIN',
                is_active=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("✓ Admin user created!")
        else:
            print("✓ Admin user already exists!")
        
        print("\n[4/4] Verifying setup...")
        employee_count = Employee.query.count()
        user_count = User.query.count()
        print(f"✓ Total employees: {employee_count}")
        print(f"✓ Total users: {user_count}")
        
        print("\n" + "=" * 60)
        print("✅ DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("   1. Start the application: python run.py")
        print("   2. Open browser: http://localhost:5000")
        print("   3. Login with:")
        print("      Username: admin")
        print("      Password: admin123")
        print("\n" + "=" * 60)
        
except Exception as e:
    print("\n❌ ERROR:", str(e))
    print("\nTroubleshooting:")
    print("1. Make sure you're in the erpportalflask directory")
    print("2. Install dependencies: pip install Flask SQLAlchemy Flask-Login Flask-WTF Flask-Bcrypt")
    print("3. Try again: python setup_database.py")
    sys.exit(1)
