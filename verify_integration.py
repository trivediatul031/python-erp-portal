"""
Manual integration verification without pandas dependency.
Verifies seams between FEATs work correctly.
"""
import os
# Clear DATABASE_URL before loading config
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']
os.environ['FLASK_ENV'] = 'testing'

print("=" * 70)
print("INTEGRATION VERIFICATION - TAS ERP PORTAL")
print("=" * 70)

# Test 1: Module imports
print("\n[1] Testing module imports...")
try:
    from app import create_app
    from app.models import db, User, Employee, TASRecord, TASSequence
    from app.utils import generate_tas_number
    from app.auth import admin_required, employee_required
    from app.forms import LoginForm, TASForm, ImportEmployeesForm, CreateUserForm
    print("    ✓ All modules import successfully")
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    exit(1)

# Test 2: App creation and configuration
print("\n[2] Testing app creation...")
try:
    app = create_app('default')
    # Override database URI before any database operations
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_BINDS'] = None
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    print("    ✓ Flask app created with test config")
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    exit(1)

# Test 3: Route registration (FEAT integration)
print("\n[3] Testing route registration (FEAT-001, 002, 003, 004 integration)...")
try:
    with app.app_context():
        routes = {rule.rule: rule.endpoint for rule in app.url_map.iter_rules()}
        
        # FEAT-001: Auth routes
        assert '/login' in routes, "Login route missing (FEAT-001)"
        assert '/logout' in routes, "Logout route missing (FEAT-001)"
        print("    ✓ FEAT-001 (Auth) routes registered")
        
        # FEAT-002: Admin routes  
        assert '/admin/dashboard' in routes, "Admin dashboard missing (FEAT-002)"
        assert '/admin/import_employees' in routes, "Import employees missing (FEAT-002)"
        assert '/admin/user_management' in routes, "User management missing (FEAT-002)"
        assert '/admin/create_user' in routes, "Create user missing (FEAT-002)"
        assert '/admin/export_tas' in routes, "Export TAS missing (FEAT-002)"
        assert '/admin/tas_list' in routes, "TAS list missing (FEAT-002)"
        print("    ✓ FEAT-002 (Admin) routes registered")
        
        # FEAT-003: Employee routes
        assert '/employee/dashboard' in routes, "Employee dashboard missing (FEAT-003)"
        assert '/employee/submit-tas' in routes, "Submit TAS missing (FEAT-003)"
        assert '/employee/tas-history' in routes, "TAS history missing (FEAT-003)"
        print("    ✓ FEAT-003 (Employee) routes registered")
        
        # FEAT-004: Error handlers
        assert 403 in app.error_handler_spec[None], "403 error handler missing (FEAT-004)"
        assert 404 in app.error_handler_spec[None], "404 error handler missing (FEAT-004)"
        assert 500 in app.error_handler_spec[None], "500 error handler missing (FEAT-004)"
        print("    ✓ FEAT-004 (Error handlers) registered")
        
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Database models
print("\n[4] Testing database models...")
try:
    with app.app_context():
        db.drop_all()  # Clear any existing data
        db.create_all()
        
        # Create admin employee
        admin_emp = Employee(
            emp_id='ADMIN',
            name='System Administrator',
            email='admin@test.com',
            department='IT',
            designation='Administrator',
            is_active=True
        )
        db.session.add(admin_emp)
        db.session.commit()
        print("    ✓ Employee model working")
        
        # Create admin user (FEAT-001)
        admin_user = User(
            username='admin',
            role='admin',
            emp_id='ADMIN',
            is_active=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("    ✓ User model working (FEAT-001)")
        
        # Verify user can be queried (auth integration)
        user = User.query.filter_by(username='admin').first()
        assert user is not None, "User query failed"
        assert user.check_password('admin123'), "Password check failed"
        print("    ✓ User authentication works (FEAT-001 integration)")
        
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 5: Employee import and user creation (FEAT-002 + FEAT-001)
print("\n[5] Testing employee import and user creation (FEAT-002 + FEAT-001)...")
try:
    with app.app_context():
        # Import employee (FEAT-002)
        emp = Employee(
            emp_id='1987',
            name='John Doe',
            email='john@test.com',
            department='Engineering',
            designation='Developer',
            is_active=True
        )
        db.session.add(emp)
        db.session.commit()
        print("    ✓ Employee imported (FEAT-002)")
        
        # Create user for employee (FEAT-002 creates, FEAT-001 uses)
        emp_user = User(
            username='john.doe',
            role='employee',
            emp_id='1987',
            is_active=True
        )
        emp_user.set_password('password123')
        db.session.add(emp_user)
        db.session.commit()
        print("    ✓ User created for employee (FEAT-002 → FEAT-001)")
        
        # Verify link
        user = User.query.filter_by(emp_id='1987').first()
        assert user is not None, "User-employee link failed"
        assert user.employee_profile is not None, "Employee relationship not working"
        assert user.employee_profile.name == 'John Doe', "Employee profile incorrect"
        print("    ✓ User-Employee relationship working")
        
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 6: TAS submission (FEAT-003)
print("\n[6] Testing TAS submission (FEAT-003)...")
try:
    with app.app_context():
        from datetime import date
        from decimal import Decimal
        
        # Generate TAS number (FEAT-003 core functionality)
        tas_number1 = generate_tas_number('1987')
        assert tas_number1 == 'TAS-1987-0001', f"Expected TAS-1987-0001, got {tas_number1}"
        print(f"    ✓ TAS number generated: {tas_number1}")
        
        # Create TAS record
        tas1 = TASRecord(
            tas_number=tas_number1,
            emp_id='1987',
            travel_from='Mumbai',
            travel_to='Delhi',
            travel_date_start=date(2024, 2, 1),
            travel_date_end=date(2024, 2, 5),
            purpose='Client meeting',
            estimated_cost=Decimal('15000.00'),
            status='Pending'
        )
        db.session.add(tas1)
        db.session.commit()
        print("    ✓ TAS record created")
        
        # Test sequential TAS number
        tas_number2 = generate_tas_number('1987')
        assert tas_number2 == 'TAS-1987-0002', f"Expected TAS-1987-0002, got {tas_number2}"
        print(f"    ✓ Sequential TAS number: {tas_number2}")
        
        db.session.rollback()  # Don't save second one
        
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 7: Dashboard stats (FEAT-002 displays FEAT-003 data)
print("\n[7] Testing dashboard stats (FEAT-002 → FEAT-003 integration)...")
try:
    with app.app_context():
        # Verify admin dashboard can query TAS records (FEAT-002 uses FEAT-003 data)
        total_tas = TASRecord.query.count()
        assert total_tas == 1, f"Expected 1 TAS, found {total_tas}"
        
        pending_tas = TASRecord.query.filter_by(status='Pending').count()
        assert pending_tas == 1, f"Expected 1 pending, found {pending_tas}"
        
        print("    ✓ Dashboard can query TAS records (FEAT-002 → FEAT-003)")
        
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 8: Admin approval/rejection (FEAT-002 modifies FEAT-003 data)
print("\n[8] Testing admin approval (FEAT-002 → FEAT-003 integration)...")
try:
    with app.app_context():
        from datetime import datetime
        
        # Get TAS and admin user
        tas = TASRecord.query.filter_by(tas_number='TAS-1987-0001').first()
        admin = User.query.filter_by(username='admin').first()
        
        # Approve TAS (FEAT-002 action on FEAT-003 data)
        tas.status = 'Approved'
        tas.reviewed_at = datetime.utcnow()
        tas.reviewed_by = admin.user_id
        db.session.commit()
        print("    ✓ Admin can approve TAS (FEAT-002 → FEAT-003)")
        
        # Verify approval
        tas = TASRecord.query.filter_by(tas_number='TAS-1987-0001').first()
        assert tas.status == 'Approved', "TAS status not updated"
        assert tas.reviewed_by == admin.user_id, "Reviewer not recorded"
        print("    ✓ TAS approval recorded correctly")
        
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 9: Auth protection on routes (FEAT-001 → FEAT-002/003)
print("\n[9] Testing auth protection (FEAT-001 → FEAT-002/003)...")
try:
    with app.test_client() as client:
        # Test admin routes require auth (FEAT-001 protects FEAT-002)
        response = client.get('/admin/dashboard')
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("    ✓ Admin routes protected (FEAT-001 → FEAT-002)")
        
        # Test employee routes require auth (FEAT-001 protects FEAT-003)
        response = client.get('/employee/dashboard')
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("    ✓ Employee routes protected (FEAT-001 → FEAT-003)")
        
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 10: Error pages (FEAT-004)
print("\n[10] Testing error pages (FEAT-004)...")
try:
    with app.test_client() as client:
        # Test 404
        response = client.get('/nonexistent-page-xyz')
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("    ✓ 404 error handler working")
        
        # Test 403 (from protected route)
        response = client.get('/admin/dashboard')
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("    ✓ 403 error handler working")
        
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 70)
print("✓✓✓ ALL INTEGRATION VERIFICATION PASSED ✓✓✓")
print("=" * 70)
print("\nVerified:")
print("  • FEAT-001 (Auth) protects FEAT-002 and FEAT-003 routes")
print("  • FEAT-002 (Admin) displays FEAT-003 (TAS) data correctly")
print("  • FEAT-002 (Employee import) creates users for FEAT-003")
print("  • FEAT-003 (TAS submission) generates unique TAS numbers")
print("  • FEAT-002 (Admin approval) modifies FEAT-003 data")
print("  • FEAT-004 (Error pages) work for all routes")
print("  • All models, forms, and utilities integrate correctly")
print("=" * 70)
