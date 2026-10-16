"""
Integration test script for TAS ERP Portal.
Tests cross-FEAT integration and complete functional flow.
"""
import os
import sys
import tempfile
import pandas as pd
from datetime import date, datetime
from decimal import Decimal

# Set up Flask app
os.environ['FLASK_ENV'] = 'testing'
from app import create_app, db
from app.models import User, Employee, TASRecord, TASSequence
from flask import Flask

def setup_test_db(app):
    """Set up fresh test database."""
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        # Create admin employee
        admin_emp = Employee(
            emp_id='ADMIN',
            name='System Administrator',
            email='admin@tas-erp.com',
            department='IT',
            designation='Administrator',
            is_active=True
        )
        db.session.add(admin_emp)
        
        # Create admin user
        admin_user = User(
            username='admin',
            role='admin',
            emp_id='ADMIN',
            is_active=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        db.session.commit()
        print("✓ Test database initialized")

def test_employee_import(app):
    """Test employee import functionality (FEAT-002)."""
    print("\n[TEST] Employee Import...")
    
    with app.app_context():
        # Create test CSV
        test_data = {
            'emp_id': ['1987', '1988', '1989'],
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'email': ['john@test.com', 'jane@test.com', 'bob@test.com'],
            'department': ['Engineering', 'Sales', 'Engineering'],
            'designation': ['Developer', 'Sales Manager', 'Senior Developer'],
            'manager_id': ['ADMIN', '1987', '1987']
        }
        df = pd.DataFrame(test_data)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            df.to_csv(f, index=False)
            temp_path = f.name
        
        try:
            # Read and import
            df_import = pd.read_csv(temp_path)
            
            success_count = 0
            for index, row in df_import.iterrows():
                emp_id = str(row['emp_id']).strip()
                name = str(row['name']).strip()
                email = str(row['email']).strip()
                department = str(row['department']).strip()
                designation = str(row['designation']).strip()
                manager_id = str(row['manager_id']).strip() if pd.notna(row['manager_id']) else None
                
                employee = Employee(
                    emp_id=emp_id,
                    name=name,
                    email=email,
                    department=department,
                    designation=designation,
                    manager_id=manager_id,
                    is_active=True
                )
                db.session.add(employee)
                db.session.commit()
                success_count += 1
            
            assert success_count == 3, f"Expected 3 employees, imported {success_count}"
            
            # Verify import
            emp_count = Employee.query.filter(Employee.emp_id != 'ADMIN').count()
            assert emp_count == 3, f"Expected 3 employees in DB, found {emp_count}"
            
            print(f"  ✓ Imported {success_count} employees successfully")
            return True
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

def test_user_creation(app):
    """Test user creation for employees (FEAT-002)."""
    print("\n[TEST] User Creation...")
    
    with app.app_context():
        # Create user for employee 1987
        user = User(
            username='john.doe',
            role='employee',
            emp_id='1987',
            is_active=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Verify user created
        created_user = User.query.filter_by(username='john.doe').first()
        assert created_user is not None, "User not created"
        assert created_user.role == 'employee', "User role incorrect"
        assert created_user.emp_id == '1987', "User emp_id incorrect"
        assert created_user.check_password('password123'), "Password not set correctly"
        
        print("  ✓ User created successfully")
        return True

def test_tas_submission(app):
    """Test TAS submission by employee (FEAT-003)."""
    print("\n[TEST] TAS Submission...")
    
    with app.app_context():
        from app.utils import generate_tas_number
        
        # Test first TAS submission for emp 1987
        tas_number1 = generate_tas_number('1987')
        assert tas_number1 == 'TAS-1987-0001', f"Expected TAS-1987-0001, got {tas_number1}"
        
        tas1 = TASRecord(
            tas_number=tas_number1,
            emp_id='1987',
            travel_from='Mumbai',
            travel_to='Delhi',
            travel_date_start=date(2024, 2, 1),
            travel_date_end=date(2024, 2, 5),
            purpose='Client meeting',
            estimated_cost=Decimal('15000.00'),
            status='Pending',
            submitted_at=datetime.utcnow()
        )
        db.session.add(tas1)
        db.session.commit()
        
        print(f"  ✓ First TAS submitted: {tas_number1}")
        
        # Test second TAS submission for same employee
        tas_number2 = generate_tas_number('1987')
        assert tas_number2 == 'TAS-1987-0002', f"Expected TAS-1987-0002, got {tas_number2}"
        
        tas2 = TASRecord(
            tas_number=tas_number2,
            emp_id='1987',
            travel_from='Delhi',
            travel_to='Bangalore',
            travel_date_start=date(2024, 3, 10),
            travel_date_end=date(2024, 3, 12),
            purpose='Training session',
            estimated_cost=Decimal('12000.00'),
            status='Pending',
            submitted_at=datetime.utcnow()
        )
        db.session.add(tas2)
        db.session.commit()
        
        print(f"  ✓ Second TAS submitted: {tas_number2}")
        
        # Verify TAS records
        tas_count = TASRecord.query.filter_by(emp_id='1987').count()
        assert tas_count == 2, f"Expected 2 TAS records, found {tas_count}"
        
        return True

def test_admin_approval(app):
    """Test admin approval/rejection (FEAT-002)."""
    print("\n[TEST] Admin Approval/Rejection...")
    
    with app.app_context():
        # Get admin user
        admin_user = User.query.filter_by(username='admin').first()
        
        # Approve first TAS
        tas1 = TASRecord.query.filter_by(tas_number='TAS-1987-0001').first()
        tas1.status = 'Approved'
        tas1.reviewed_at = datetime.utcnow()
        tas1.reviewed_by = admin_user.user_id
        db.session.commit()
        
        print("  ✓ TAS-1987-0001 approved")
        
        # Reject second TAS
        tas2 = TASRecord.query.filter_by(tas_number='TAS-1987-0002').first()
        tas2.status = 'Rejected'
        tas2.reviewed_at = datetime.utcnow()
        tas2.reviewed_by = admin_user.user_id
        tas2.rejection_reason = 'Budget exceeded for this quarter'
        db.session.commit()
        
        print("  ✓ TAS-1987-0002 rejected")
        
        return True

def test_dashboard_stats(app):
    """Test dashboard statistics (FEAT-002)."""
    print("\n[TEST] Dashboard Statistics...")
    
    with app.app_context():
        # Verify total TAS count
        total_tas = TASRecord.query.count()
        assert total_tas == 2, f"Expected 2 TAS records, found {total_tas}"
        
        # Verify pending count
        pending_count = TASRecord.query.filter_by(status='Pending').count()
        assert pending_count == 0, f"Expected 0 pending, found {pending_count}"
        
        # Verify approved count
        approved_count = TASRecord.query.filter_by(status='Approved').count()
        assert approved_count == 1, f"Expected 1 approved, found {approved_count}"
        
        # Verify rejected count
        rejected_count = TASRecord.query.filter_by(status='Rejected').count()
        assert rejected_count == 1, f"Expected 1 rejected, found {rejected_count}"
        
        print(f"  ✓ Dashboard stats correct: {total_tas} total, {approved_count} approved, {rejected_count} rejected")
        
        return True

def test_data_export(app):
    """Test data export functionality (FEAT-002)."""
    print("\n[TEST] Data Export...")
    
    with app.app_context():
        # Query TAS records with employee join
        results = db.session.query(
            TASRecord.tas_number,
            TASRecord.emp_id,
            Employee.name,
            Employee.email,
            Employee.department,
            Employee.designation,
            TASRecord.travel_from,
            TASRecord.travel_to,
            TASRecord.travel_date_start,
            TASRecord.travel_date_end,
            TASRecord.purpose,
            TASRecord.estimated_cost,
            TASRecord.status,
            TASRecord.submitted_at,
            TASRecord.reviewed_at
        ).join(Employee, TASRecord.emp_id == Employee.emp_id).all()
        
        assert len(results) == 2, f"Expected 2 records for export, found {len(results)}"
        
        # Create DataFrame
        columns = ['TAS Number', 'Employee ID', 'Employee Name', 'Email', 'Department', 
                  'Designation', 'From', 'To', 'Start Date', 'End Date', 'Purpose', 
                  'Estimated Cost', 'Status', 'Submitted At', 'Reviewed At']
        df = pd.DataFrame(results, columns=columns)
        
        # Test export to CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            df.to_csv(f, index=False)
            temp_csv = f.name
        
        try:
            assert os.path.exists(temp_csv), "CSV export failed"
            
            # Verify CSV content
            df_read = pd.read_csv(temp_csv)
            assert len(df_read) == 2, "CSV has incorrect row count"
            assert 'TAS-1987-0001' in df_read['TAS Number'].values, "TAS-1987-0001 not in export"
            assert 'TAS-1987-0002' in df_read['TAS Number'].values, "TAS-1987-0002 not in export"
            
            print("  ✓ Data export successful (CSV)")
            
        finally:
            if os.path.exists(temp_csv):
                os.unlink(temp_csv)
        
        # Test export to Excel
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as f:
            df.to_excel(f, index=False, engine='openpyxl')
            temp_xlsx = f.name
        
        try:
            assert os.path.exists(temp_xlsx), "Excel export failed"
            
            # Verify Excel content
            df_read = pd.read_excel(temp_xlsx)
            assert len(df_read) == 2, "Excel has incorrect row count"
            
            print("  ✓ Data export successful (Excel)")
            
        finally:
            if os.path.exists(temp_xlsx):
                os.unlink(temp_xlsx)
        
        return True

def test_auth_protection(app):
    """Test that auth protects routes (FEAT-001 integration)."""
    print("\n[TEST] Auth Protection...")
    
    with app.test_client() as client:
        # Test that admin routes require login
        response = client.get('/admin/dashboard')
        assert response.status_code == 403, "Admin dashboard should require auth"
        
        # Test that employee routes require login
        response = client.get('/employee/dashboard')
        assert response.status_code == 403, "Employee dashboard should require auth"
        
        print("  ✓ Routes protected by authentication")
        
        return True

def test_error_pages(app):
    """Test error pages (FEAT-004)."""
    print("\n[TEST] Error Pages...")
    
    with app.test_client() as client:
        # Test 404
        response = client.get('/nonexistent-page')
        assert response.status_code == 404, "Should return 404"
        assert b'404' in response.data or b'Not Found' in response.data, "404 page not rendered"
        
        # Test 403 (accessing protected route)
        response = client.get('/admin/dashboard')
        assert response.status_code == 403, "Should return 403"
        
        print("  ✓ Error pages working")
        
        return True

def main():
    """Run all integration tests."""
    print("=" * 60)
    print("TAS ERP PORTAL - INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Create test app with SQLite
    app = create_app('default')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    try:
        # Run tests
        setup_test_db(app)
        
        tests = [
            test_employee_import,
            test_user_creation,
            test_tas_submission,
            test_admin_approval,
            test_dashboard_stats,
            test_data_export,
            test_auth_protection,
            test_error_pages
        ]
        
        passed = 0
        failed = 0
        
        for test_func in tests:
            try:
                if test_func(app):
                    passed += 1
            except Exception as e:
                print(f"  ✗ FAILED: {str(e)}")
                import traceback
                traceback.print_exc()
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"RESULTS: {passed} passed, {failed} failed")
        print("=" * 60)
        
        if failed == 0:
            print("\n✓ ALL INTEGRATION TESTS PASSED")
            return 0
        else:
            print(f"\n✗ {failed} TEST(S) FAILED")
            return 1
            
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
