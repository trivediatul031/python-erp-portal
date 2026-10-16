# Quick Start Guide - TAS ERP Portal

## ✅ Easy Setup (No MySQL Required!)

I've configured the portal to use **SQLite** instead of MySQL, so you don't need to install anything extra!

### Method 1: Double-click Batch File (Easiest!)

1. **Double-click** `START_PORTAL.bat` in the `erpportalflask` folder
2. Wait for dependencies to install (takes 1-2 minutes first time)
3. Portal will automatically start
4. Open browser: http://localhost:5000
5. Login: `admin` / `admin123`

### Method 2: Manual Commands

Open Command Prompt or PowerShell in the `erpportalflask` folder and run:

```bash
# Install dependencies (one-time only)
pip install Flask SQLAlchemy Flask-Login Flask-WTF Flask-Bcrypt pandas openpyxl python-dotenv Werkzeug

# Create database (one-time only)
python init_db.py

# Start the portal
python run.py
```

## 🌐 Accessing the Portal

Once started, open your web browser and go to:

**http://localhost:5000**

or

**http://127.0.0.1:5000**

## 🔐 Login Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin123`

## 📊 What You'll See

### Admin Dashboard
- **Purple Card**: Total TAS Submissions
- **Green Card**: Pending Approvals
- **Blue Card**: Approved Count
- **Orange Card**: Rejected Count
- **Chart**: TAS submissions over time
- **Status Panel**: Progress bars
- **Table**: Recent submissions

### Navigation Menu (Left Sidebar)
- Dashboard
- Import Employees
- TAS Records
- User Management

## 🧪 Testing the Portal

### 1. Import Sample Employees
1. Click "Import Employees" in sidebar
2. Upload `sample_employees.csv`
3. See 5 employees imported

### 2. Create Employee User
To test employee features, create a user account:

```python
# Run this in Python console or create a script
from app import create_app
from app.models import db, User

app = create_app()
with app.app_context():
    user = User(username='john.doe', role='employee', emp_id='1987', is_active=True)
    user.set_password('test123')
    db.session.add(user)
    db.session.commit()
    print("Employee user created!")
```

Or create a file `create_employee_user.py`:

```python
from app import create_app
from app.models import db, User

app = create_app()
with app.app_context():
    # Create user for employee 1987 (from sample data)
    user = User(
        username='john.doe',
        role='employee',
        emp_id='1987',
        is_active=True
    )
    user.set_password('test123')
    db.session.add(user)
    db.session.commit()
    print("✓ Employee user created!")
    print("Username: john.doe")
    print("Password: test123")
```

Then run: `python create_employee_user.py`

### 3. Submit TAS as Employee
1. Logout from admin
2. Login as: `john.doe` / `test123`
3. Click "Submit TAS"
4. Fill form and submit
5. See TAS number: `TAS-1987-0001`

### 4. Approve TAS as Admin
1. Logout and login as admin
2. Go to "TAS Records"
3. Find the submitted TAS
4. Click "Approve"

## 🛑 Stopping the Portal

Press `Ctrl + C` in the terminal/command prompt where Flask is running

## 📁 Database Location

The SQLite database is created as:
`c:\Users\AtulTrivedi\erpportalflask\instance\tas_erp.db`

## ❓ Troubleshooting

### Error: Module not found
Run: `pip install Flask SQLAlchemy Flask-Login Flask-WTF Flask-Bcrypt pandas openpyxl python-dotenv`

### Error: Cannot import app
Make sure you're in the correct directory: `cd c:\Users\AtulTrivedi\erpportalflask`

### Port 5000 already in use
Stop any other Flask apps or use a different port:
`python run.py --port 5001`

### Database locked error
Close all Python processes and restart

## ✨ Features Available Now

✅ Admin Dashboard (modern UI matching your reference)
✅ Employee management
✅ Import employees from CSV/Excel
✅ Export TAS records
✅ Submit TAS requests
✅ Approve/Reject TAS
✅ Automatic TAS number generation (TAS-1987-0001)
✅ Role-based access control
✅ Charts and statistics

## 🎯 Next Steps

1. Start the portal using batch file
2. Explore admin dashboard
3. Import sample employees
4. Create employee user accounts
5. Test TAS workflow

---

**Need MySQL Instead of SQLite?**

If you want to use MySQL later:
1. Install MySQL
2. Edit `config.py` to change database URL
3. Run `schema.sql` to create tables

---

Enjoy your TAS ERP Portal! 🚀
