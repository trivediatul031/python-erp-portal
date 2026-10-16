"""Simple test to verify Flask app can start."""
import os
os.environ['FLASK_ENV'] = 'testing'

try:
    from app import create_app
    app = create_app('default')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    print("✓ Flask app created successfully")
    
    # Test routes are registered
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    print(f"✓ Found {len(routes)} routes")
    
    # Check key routes exist
    assert '/login' in routes, "Login route missing"
    assert '/admin/dashboard' in routes, "Admin dashboard missing"
    assert '/employee/dashboard' in routes, "Employee dashboard missing"
    assert '/admin/import_employees' in routes, "Import employees missing"
    assert '/employee/submit-tas' in routes, "Submit TAS missing"
    
    print("✓ All key routes registered")
    
    # Test database models
    from app.models import User, Employee, TASRecord, TASSequence
    print("✓ All models imported successfully")
    
    # Test utils
    from app.utils import generate_tas_number
    print("✓ Utils imported successfully")
    
    # Test decorators
    from app.auth import admin_required, employee_required
    print("✓ Auth decorators imported successfully")
    
    # Test forms
    from app.forms import LoginForm, TASForm, ImportEmployeesForm, CreateUserForm
    print("✓ All forms imported successfully")
    
    print("\n✓✓✓ ALL BASIC CHECKS PASSED ✓✓✓")
    
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
