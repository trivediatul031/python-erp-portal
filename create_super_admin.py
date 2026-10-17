"""
Create a separate super admin account with access to all employee data and TAS records
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Employee, TASRecord, bcrypt

def main():
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("CREATING SUPER ADMIN ACCOUNT")
        print("=" * 60)
        
        # Delete old admin if exists
        old_admin = User.query.filter_by(username='admin').first()
        if old_admin:
            db.session.delete(old_admin)
            print("✅ Deleted old admin account")
        
        # Create new super admin (NOT linked to any employee)
        admin_username = 'admin'
        admin_password = 'admin123'
        
        super_admin = User(
            username=admin_username,
            password_hash=bcrypt.generate_password_hash(admin_password).decode('utf-8'),
            role='admin',
            emp_id=None,  # NOT an employee
            is_active=True
        )
        
        db.session.add(super_admin)
        db.session.commit()
        
        print("\n✅ SUPER ADMIN CREATED SUCCESSFULLY!")
        print("\n" + "=" * 60)
        print("SUPER ADMIN LOGIN CREDENTIALS")
        print("=" * 60)
        print(f"Username: {admin_username}")
        print(f"Password: {admin_password}")
        print(f"Role: Super Admin (NOT an employee)")
        print(f"Employee ID: None (standalone admin)")
        print("\n" + "=" * 60)
        print("ADMIN CAPABILITIES")
        print("=" * 60)
        print("✅ Access ALL employee records")
        print("✅ Access ALL TAS submissions from ALL employees")
        print("✅ View employee list with login credentials")
        print("✅ Import employees")
        print("✅ Create users")
        print("✅ Search and filter all data")
        print("\n" + "=" * 60)
        print("HOW TO LOGIN")
        print("=" * 60)
        print("1. Go to: http://127.0.0.1:5000/login")
        print(f"2. Enter Username: {admin_username}")
        print(f"3. Enter Password: {admin_password}")
        print("4. Click Login")
        print("5. You'll be redirected to: http://127.0.0.1:5000/admin/dashboard")
        print("\n" + "=" * 60)
        print("ADMIN DASHBOARD PAGES")
        print("=" * 60)
        print("📊 Dashboard: http://127.0.0.1:5000/admin/dashboard")
        print("👥 Employee List: http://127.0.0.1:5000/admin/employee_list")
        print("📤 Import Employees: http://127.0.0.1:5000/admin/import_employees")
        print("\n" + "=" * 60)
        
        # Show statistics
        total_employees = Employee.query.count()
        total_tas = TASRecord.query.count()
        total_users = User.query.filter_by(role='employee').count()
        
        print("CURRENT SYSTEM STATUS")
        print("=" * 60)
        print(f"📊 Total Employees: {total_employees}")
        print(f"📋 Total TAS Records: {total_tas}")
        print(f"👤 Total Employee Users: {total_users}")
        print(f"👑 Super Admin Users: 1")
        print("\n✅ Admin can access ALL of this data!")
        print("=" * 60)

if __name__ == '__main__':
    main()
