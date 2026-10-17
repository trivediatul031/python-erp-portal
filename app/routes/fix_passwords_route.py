"""Route to create super admin and fix passwords"""
from flask import Blueprint, jsonify, render_template_string
from flask_login import current_user
from app.models import db, User, Employee, TASRecord, bcrypt

fix_bp = Blueprint('fix', __name__)

@fix_bp.route('/check-my-login')
def check_my_login():
    """Check current user login status"""
    if current_user.is_authenticated:
        return jsonify({
            'logged_in': True,
            'username': current_user.username,
            'role': current_user.role,
            'emp_id': current_user.emp_id,
            'is_active': current_user.is_active,
            'user_id': current_user.user_id,
            'is_admin': current_user.role == 'admin',
            'should_see': 'Admin Dashboard' if current_user.role == 'admin' else 'Employee Dashboard'
        })
    else:
        return jsonify({
            'logged_in': False,
            'message': 'Not logged in'
        })

@fix_bp.route('/fix-all-passwords-bcrypt')
def fix_all_passwords_bcrypt():
    """Fix ALL user passwords to use bcrypt hashing"""
    try:
        # Get all users
        all_users = User.query.all()
        
        updated = 0
        admin_count = 0
        employee_count = 0
        
        for user in all_users:
            if user.username == 'admin':
                # Fix admin
                user.password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
                user.role = 'admin'
                user.emp_id = None
                user.is_active = True
                admin_count += 1
            else:
                # Fix employee - password format: [emp_code]emp@123
                password = f"{user.username}emp@123"
                user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
                user.role = 'employee'
                user.is_active = True
                employee_count += 1
            
            updated += 1
        
        db.session.commit()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>All Passwords Fixed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 30px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .box {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin: 20px 0;
                }}
                .success {{ border-left: 5px solid #28a745; }}
                .info {{ border-left: 5px solid #17a2b8; }}
                h1 {{ color: #28a745; margin-top: 0; }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background: #f8f9fa;
                    font-weight: bold;
                }}
                code {{
                    background: #f8f9fa;
                    padding: 2px 6px;
                    border-radius: 3px;
                    color: #d9534f;
                    font-size: 14px;
                }}
                .btn {{
                    display: inline-block;
                    background: #007bff;
                    color: white;
                    padding: 15px 40px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 18px;
                    font-weight: bold;
                    margin: 10px;
                }}
                .btn:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <div class="box success">
                <h1>✅ All Passwords Fixed with Bcrypt!</h1>
                <p style="font-size: 18px;">
                    <strong>Total Users Updated:</strong> {updated}<br>
                    <strong>Admin Accounts:</strong> {admin_count}<br>
                    <strong>Employee Accounts:</strong> {employee_count}
                </p>
            </div>
            
            <div class="box info">
                <h2>🔐 Login Credentials</h2>
                
                <h3>Admin Login</h3>
                <table>
                    <tr>
                        <th>Username</th>
                        <th>Password</th>
                        <th>Access</th>
                    </tr>
                    <tr>
                        <td><code>admin</code></td>
                        <td><code>admin123</code></td>
                        <td>Admin Dashboard - All employee data & TAS</td>
                    </tr>
                </table>
                
                <h3>Employee Login Format</h3>
                <table>
                    <tr>
                        <th>Username</th>
                        <th>Password</th>
                        <th>Example</th>
                    </tr>
                    <tr>
                        <td><code>[Employee Code]</code></td>
                        <td><code>[Code]emp@123</code></td>
                        <td>Username: <code>1009</code><br>Password: <code>1009emp@123</code></td>
                    </tr>
                </table>
                
                <h3>Sample Employee Logins</h3>
                <table>
                    <tr>
                        <th>Emp Code</th>
                        <th>Name</th>
                        <th>Username</th>
                        <th>Password</th>
                    </tr>
                    <tr>
                        <td>1009</td>
                        <td>Sandipan Sensarma</td>
                        <td><code>1009</code></td>
                        <td><code>1009emp@123</code></td>
                    </tr>
                    <tr>
                        <td>1018</td>
                        <td>Manan Jaisinghani</td>
                        <td><code>1018</code></td>
                        <td><code>1018emp@123</code></td>
                    </tr>
                    <tr>
                        <td>1020</td>
                        <td>Srividhya</td>
                        <td><code>1020</code></td>
                        <td><code>1020emp@123</code></td>
                    </tr>
                </table>
            </div>
            
            <div class="box info">
                <h2>🚀 Try Login Now</h2>
                <center>
                    <a href="/login" class="btn">GO TO LOGIN PAGE →</a>
                </center>
                
                <h3 style="margin-top: 30px;">Test These Logins:</h3>
                <ol style="font-size: 16px; line-height: 1.8;">
                    <li><strong>Admin:</strong> Username: <code>admin</code>, Password: <code>admin123</code>
                        <br>→ Should redirect to <code>/admin/dashboard</code></li>
                    <li><strong>Employee 1009:</strong> Username: <code>1009</code>, Password: <code>1009emp@123</code>
                        <br>→ Should redirect to <code>/employee/dashboard</code></li>
                </ol>
            </div>
            
            <div class="box" style="background: #d4edda; border-left: 5px solid #28a745;">
                <h3 style="margin-top: 0; color: #155724;">✅ All {employee_count} Employee Passwords Updated!</h3>
                <p>Every employee can now login with:</p>
                <ul>
                    <li>Username = Their employee code (e.g., 1009, 1018, 1020...)</li>
                    <li>Password = [their code]emp@123 (e.g., 1009emp@123)</li>
                </ul>
                <p><strong>All passwords are now using bcrypt hashing and will work correctly!</strong></p>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

@fix_bp.route('/fix-admin-complete')
def fix_admin_complete():
    """Complete admin fix with debug info"""
    from flask import session
    from flask_login import logout_user
    
    try:
        # Step 1: Fix admin in database
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            admin = User(
                username='admin',
                password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                role='admin',
                emp_id=None,
                is_active=True
            )
            db.session.add(admin)
            status = "Created new admin"
        else:
            old_role = admin.role
            old_emp_id = admin.emp_id
            
            admin.username = 'admin'
            admin.password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin.role = 'admin'
            admin.emp_id = None
            admin.is_active = True
            
            status = f"Updated admin (was role={old_role}, emp_id={old_emp_id})"
        
        db.session.commit()
        
        # Step 2: Logout current user
        logout_user()
        session.clear()
        
        # Step 3: Verify admin in database
        admin_check = User.query.filter_by(username='admin').first()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Fixed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 700px;
                    margin: 30px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .box {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin: 20px 0;
                }}
                .success {{ border-left: 5px solid #28a745; }}
                .info {{ border-left: 5px solid #17a2b8; }}
                h1 {{ color: #28a745; margin-top: 0; }}
                h2 {{ color: #17a2b8; }}
                .btn {{
                    display: inline-block;
                    background: #007bff;
                    color: white;
                    padding: 15px 40px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 20px;
                    font-weight: bold;
                }}
                .btn:hover {{ background: #0056b3; }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                td:first-child {{
                    font-weight: bold;
                    width: 40%;
                }}
                code {{
                    background: #f8f9fa;
                    padding: 2px 6px;
                    border-radius: 3px;
                    color: #d9534f;
                }}
            </style>
        </head>
        <body>
            <div class="box success">
                <h1>✅ Admin Account Fixed Successfully!</h1>
                <p><strong>Status:</strong> {status}</p>
                <p><strong>You have been logged out.</strong></p>
            </div>
            
            <div class="box info">
                <h2>📊 Admin Account Verification</h2>
                <table>
                    <tr>
                        <td>Username:</td>
                        <td><code>{admin_check.username}</code></td>
                    </tr>
                    <tr>
                        <td>Role:</td>
                        <td><code>{admin_check.role}</code></td>
                    </tr>
                    <tr>
                        <td>Employee ID:</td>
                        <td><code>{admin_check.emp_id if admin_check.emp_id else 'NULL (Standalone Admin)'}</code></td>
                    </tr>
                    <tr>
                        <td>Is Active:</td>
                        <td><code>{admin_check.is_active}</code></td>
                    </tr>
                    <tr>
                        <td>Password:</td>
                        <td><code>admin123</code> (bcrypt hashed)</td>
                    </tr>
                </table>
            </div>
            
            <div class="box info">
                <h2>🚀 Next Steps</h2>
                <ol style="font-size: 16px; line-height: 1.8;">
                    <li>Click the button below to go to login page</li>
                    <li>Enter username: <code>admin</code></li>
                    <li>Enter password: <code>admin123</code></li>
                    <li>Click Login</li>
                    <li><strong>You will be redirected to ADMIN DASHBOARD</strong> (not employee dashboard!)</li>
                </ol>
            </div>
            
            <center>
                <a href="/login" class="btn">GO TO LOGIN PAGE →</a>
            </center>
            
            <div class="box" style="background: #fff3cd; border-left: 5px solid #ffc107; margin-top: 20px;">
                <h3 style="margin-top: 0;">⚠️ Important</h3>
                <p>After login, the URL should be:</p>
                <p><code>http://127.0.0.1:5000/admin/dashboard</code></p>
                <p><strong>NOT</strong> <code>/employee/dashboard</code></p>
                <p>If you still see employee dashboard, take a screenshot and let me know!</p>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

@fix_bp.route('/fix-admin-account-now')
def fix_admin_account_now():
    """Fix admin account to have NULL emp_id and proper role"""
    try:
        # Find admin user
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            # Create admin if doesn't exist
            admin = User(
                username='admin',
                password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                role='admin',
                emp_id=None,
                is_active=True
            )
            db.session.add(admin)
        else:
            # Fix existing admin
            admin.password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin.role = 'admin'
            admin.emp_id = None  # IMPORTANT: NULL, not 'ADMIN'
            admin.is_active = True
        
        db.session.commit()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Fixed</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                    text-align: center;
                }
                .success {
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { color: #28a745; }
                .btn {
                    display: inline-block;
                    background: #007bff;
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px;
                    font-size: 18px;
                }
                .btn:hover { background: #0056b3; }
                .logout-btn { background: #dc3545; }
                .logout-btn:hover { background: #c82333; }
            </style>
        </head>
        <body>
            <div class="success">
                <h1>✅ Admin Account Fixed!</h1>
                <p style="font-size: 18px; margin: 20px 0;">
                    Admin account is now properly configured as a super admin.
                </p>
                <div style="background: #e7f3ff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Next Steps:</h3>
                    <ol style="text-align: left;">
                        <li>Click "Logout" below</li>
                        <li>Login again with: <strong>admin</strong> / <strong>admin123</strong></li>
                        <li>You'll see the <strong>Admin Dashboard</strong> with all employee data!</li>
                    </ol>
                </div>
                <a href="/logout" class="btn logout-btn">Logout Now</a>
                <br><br>
                <small style="color: #666;">After logout, go to /login and login again as admin</small>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

@fix_bp.route('/create-super-admin-now')
def create_super_admin():
    """Create separate super admin account with access to all data"""
    try:
        # Delete old admin if exists
        old_admins = User.query.filter_by(role='admin').all()
        for old_admin in old_admins:
            db.session.delete(old_admin)
        
        # Create new super admin (NOT linked to any employee)
        admin_username = 'admin'
        admin_password = 'admin123'
        
        super_admin = User(
            username=admin_username,
            password_hash=bcrypt.generate_password_hash(admin_password).decode('utf-8'),
            role='admin',
            emp_id=None,  # NOT an employee - standalone admin
            is_active=True
        )
        
        db.session.add(super_admin)
        db.session.commit()
        
        # Get statistics
        total_employees = Employee.query.count()
        total_tas = TASRecord.query.count()
        total_users = User.query.filter_by(role='employee').count()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Super Admin Created</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .success-box {{
                    background: white;
                    border-left: 5px solid #28a745;
                    padding: 30px;
                    border-radius: 5px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #28a745;
                    margin-top: 0;
                }}
                .credentials {{
                    background: #e7f3ff;
                    border: 2px solid #0066cc;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .credentials h2 {{
                    margin-top: 0;
                    color: #0066cc;
                }}
                .cred-item {{
                    font-size: 18px;
                    margin: 10px 0;
                }}
                .cred-item strong {{
                    display: inline-block;
                    width: 120px;
                }}
                .stats {{
                    background: #fff3cd;
                    border: 2px solid #ffc107;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .access-list {{
                    background: #d4edda;
                    border: 2px solid #28a745;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .access-list li {{
                    margin: 8px 0;
                    font-size: 16px;
                }}
                .login-button {{
                    display: inline-block;
                    background: #0066cc;
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 18px;
                    font-weight: bold;
                    margin-top: 20px;
                }}
                .login-button:hover {{
                    background: #0052a3;
                }}
            </style>
        </head>
        <body>
            <div class="success-box">
                <h1>✅ Super Admin Account Created Successfully!</h1>
                
                <div class="credentials">
                    <h2>🔐 Super Admin Login Credentials</h2>
                    <div class="cred-item"><strong>Username:</strong> <code style="font-size: 20px; color: #d9534f;">{admin_username}</code></div>
                    <div class="cred-item"><strong>Password:</strong> <code style="font-size: 20px; color: #d9534f;">{admin_password}</code></div>
                    <div class="cred-item"><strong>Role:</strong> Super Admin (NOT an employee)</div>
                    <div class="cred-item"><strong>Employee ID:</strong> None (standalone admin)</div>
                </div>
                
                <div class="access-list">
                    <h2>✅ Admin Capabilities</h2>
                    <ul>
                        <li>✅ <strong>Access ALL {total_employees} employee records</strong></li>
                        <li>✅ <strong>Access ALL {total_tas} TAS submissions from ALL employees</strong></li>
                        <li>✅ View employee list with login credentials</li>
                        <li>✅ Import employees from CSV/Excel</li>
                        <li>✅ Create new user accounts</li>
                        <li>✅ Search and filter all data</li>
                        <li>✅ View statistics and charts</li>
                    </ul>
                </div>
                
                <div class="stats">
                    <h2>📊 Current System Status</h2>
                    <div class="cred-item"><strong>Total Employees:</strong> {total_employees}</div>
                    <div class="cred-item"><strong>Total TAS Records:</strong> {total_tas}</div>
                    <div class="cred-item"><strong>Employee Users:</strong> {total_users}</div>
                    <div class="cred-item"><strong>Super Admins:</strong> 1</div>
                </div>
                
                <h2>🚀 How to Login</h2>
                <ol>
                    <li>Click the button below to go to login page</li>
                    <li>Enter Username: <strong>{admin_username}</strong></li>
                    <li>Enter Password: <strong>{admin_password}</strong></li>
                    <li>Click "Login"</li>
                    <li>You'll be redirected to the Admin Dashboard</li>
                </ol>
                
                <center>
                    <a href="/login" class="login-button">GO TO LOGIN PAGE →</a>
                </center>
                
                <h2 style="margin-top: 30px;">📋 Admin Dashboard Pages</h2>
                <ul>
                    <li><strong>Dashboard:</strong> <a href="/admin/dashboard">/admin/dashboard</a> (All TAS records)</li>
                    <li><strong>Employee List:</strong> <a href="/admin/employee_list">/admin/employee_list</a> (All employees)</li>
                    <li><strong>Import Employees:</strong> <a href="/admin/import_employees">/admin/import_employees</a></li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500
