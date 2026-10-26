#!/usr/bin/env python3
"""
Integration test script for Microsoft Entra ID SSO implementation.
Tests cross-FEAT integration and startup verification.
"""
import os
import sys

# Set development environment
os.environ['FLASK_ENV'] = 'development'
# Use absolute path for database
db_path = os.path.join(os.getcwd(), 'instance', 'tas_erp.db')
os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

print("=" * 70)
print(" INTEGRATION VERIFICATION TEST")
print("=" * 70)

# Test 1: Module Imports
print("\n[TEST 1] Module Imports")
print("-" * 70)
try:
    from app import create_app, db
    from app.models import Employee, User, TASRecord, TASSequence
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.employee import employee_bp
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Flask App Creation
print("\n[TEST 2] Flask App Creation")
print("-" * 70)
try:
    app = create_app()
    print(f"✓ App created: {app.name}")
    print(f"✓ Config loaded: {app.config.get('FLASK_ENV')}")
except Exception as e:
    print(f"✗ App creation failed: {e}")
    sys.exit(1)

# Test 3: Azure Configuration
print("\n[TEST 3] Azure AD Configuration")
print("-" * 70)
with app.app_context():
    try:
        tenant_id = app.config.get('AZURE_TENANT_ID')
        client_id = app.config.get('AZURE_CLIENT_ID')
        client_secret = app.config.get('AZURE_CLIENT_SECRET')
        app_url = app.config.get('APP_URL')
        redirect_uri = app.config.get('AZURE_REDIRECT_URI')
        authority = app.config.get('AZURE_AUTHORITY')
        
        print(f"  AZURE_TENANT_ID: {'✓ Set' if tenant_id else '✗ Missing'}")
        print(f"  AZURE_CLIENT_ID: {'✓ Set' if client_id else '✗ Missing'}")
        print(f"  AZURE_CLIENT_SECRET: {'✓ Set (' + client_secret[:8] + '...)' if client_secret else '✗ Missing'}")
        print(f"  APP_URL: {app_url if app_url else '✗ Missing'}")
        print(f"  AZURE_REDIRECT_URI: {redirect_uri if redirect_uri else '✗ Missing'}")
        print(f"  AZURE_AUTHORITY: {authority if authority else '✗ Missing'}")
        
        if all([tenant_id, client_id, client_secret, app_url, redirect_uri, authority]):
            print("✓ Azure AD configuration complete")
        else:
            print("✗ Azure AD configuration incomplete")
    except Exception as e:
        print(f"✗ Configuration check failed: {e}")

# Test 4: Route Registration
print("\n[TEST 4] Route Registration")
print("-" * 70)
with app.app_context():
    try:
        # Get all routes
        auth_routes = []
        admin_routes = []
        employee_routes = []
        
        for rule in app.url_map.iter_rules():
            if 'auth' in rule.rule or 'microsoft' in rule.rule.lower():
                auth_routes.append(rule.rule)
            elif 'admin' in rule.rule:
                admin_routes.append(rule.rule)
            elif 'employee' in rule.rule:
                employee_routes.append(rule.rule)
        
        print("  Auth Routes:")
        for route in sorted(set(auth_routes)):
            print(f"    {route}")
        
        print("\n  Admin Routes (sample):")
        for route in sorted(set(admin_routes))[:5]:
            print(f"    {route}")
        
        print("\n  Employee Routes (sample):")
        for route in sorted(set(employee_routes))[:5]:
            print(f"    {route}")
        
        # Check critical routes
        critical_routes = ['/login', '/auth/microsoft', '/auth/Microsoft/callback', '/logout']
        missing_routes = []
        
        for route in critical_routes:
            found = any(route in str(rule.rule) for rule in app.url_map.iter_rules())
            if not found:
                missing_routes.append(route)
        
        if missing_routes:
            print(f"\n✗ Missing critical routes: {missing_routes}")
        else:
            print("\n✓ All critical auth routes registered")
    except Exception as e:
        print(f"✗ Route registration check failed: {e}")

# Test 5: Database Models
print("\n[TEST 5] Database Models")
print("-" * 70)
with app.app_context():
    try:
        # Create tables
        db.create_all()
        print("✓ Database tables created")
        
        # Test Employee model
        test_emp = Employee.query.filter_by(emp_id='TEST001').first()
        if not test_emp:
            test_emp = Employee(
                emp_id='TEST001',
                name='Test Employee',
                email='test@example.com',
                department='IT',
                designation='Developer',
                is_active=True
            )
            db.session.add(test_emp)
            db.session.commit()
            print("✓ Employee model works (created test employee)")
        else:
            print("✓ Employee model works (test employee exists)")
        
        # Test User model
        test_user = User.query.filter_by(username='test@example.com').first()
        if not test_user:
            from app.models import bcrypt
            test_user = User(
                username='test@example.com',
                password_hash=bcrypt.generate_password_hash('test123').decode('utf-8'),
                role='employee',
                emp_id='TEST001',
                is_active=True
            )
            db.session.add(test_user)
            db.session.commit()
            print("✓ User model works (created test user)")
        else:
            print("✓ User model works (test user exists)")
        
    except Exception as e:
        print(f"✗ Database models check failed: {e}")
        import traceback
        traceback.print_exc()

# Test 6: Email Index Verification
print("\n[TEST 6] Email Index Verification")
print("-" * 70)
with app.app_context():
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        indexes = inspector.get_indexes('employees')
        
        print("  Indexes on employees table:")
        for idx in indexes:
            print(f"    - {idx['name']}: {idx['column_names']}")
        
        has_email_index = any(
            'email' in str(idx.get('column_names', [])).lower() or 
            'email' in idx.get('name', '').lower()
            for idx in indexes
        )
        
        if has_email_index:
            print("✓ Email index exists")
        else:
            print("⚠ Email index missing (will create)")
            db.session.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_employee_email_lower 
                ON employees(LOWER(email));
            """))
            db.session.commit()
            print("✓ Email index created")
    except Exception as e:
        print(f"⚠ Index verification skipped: {e}")

# Test 7: MSAL Library
print("\n[TEST 7] MSAL Library")
print("-" * 70)
try:
    import msal
    print(f"✓ MSAL library installed (version {msal.__version__})")
    
    # Test MSAL client creation
    with app.app_context():
        from app.routes.auth import get_msal_client
        try:
            msal_client = get_msal_client()
            print("✓ MSAL client can be created")
        except Exception as e:
            print(f"⚠ MSAL client creation issue: {e}")
except ImportError:
    print("✗ MSAL library not installed")

# Test 8: Logs Directory
print("\n[TEST 8] Logs Directory")
print("-" * 70)
if os.path.exists('logs'):
    print("✓ Logs directory exists")
    if os.access('logs', os.W_OK):
        print("✓ Logs directory is writable")
    else:
        print("✗ Logs directory is not writable")
else:
    print("✗ Logs directory missing")

print("\n" + "=" * 70)
print(" INTEGRATION VERIFICATION COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("1. Review any ✗ or ⚠ items above")
print("2. Register redirect URI in Azure Portal:")
print(f"   {app.config.get('AZURE_REDIRECT_URI')}")
print("3. Start the application: flask run")
print("4. Test SSO login at: http://localhost:5000/login")
