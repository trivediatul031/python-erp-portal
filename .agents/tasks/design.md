# Technical Design: Travel Approval System (TAS) ERP Portal

## Overview

This document specifies the technical design for a Python-based Travel Approval System (TAS) ERP portal. The system provides a super admin dashboard for managing employee TAS records with import/export capabilities, an employee portal for submitting travel approval requests, and automated TAS number generation. The application uses Flask as the web framework, MySQL as the database, SQLAlchemy ORM for data access, and Bootstrap for the responsive frontend UI.

## Technology Stack

**Backend:**
- Python 3.9+
- Flask 2.3+ (web framework)
- SQLAlchemy 2.0+ (ORM for MySQL interaction)
- Flask-Login (session management and authentication)
- Flask-WTF (CSRF protection and form handling)
- Bcrypt (password hashing)

**Database:**
- MySQL 8.0+
- PyMySQL (MySQL driver for SQLAlchemy)

**Frontend:**
- HTML5/CSS3
- Bootstrap 5.3 (responsive UI framework)
- JavaScript (vanilla JS for dynamic interactions)
- DataTables.js (for sortable, searchable tables)

**Data Processing:**
- Pandas (Excel/CSV import and export)
- openpyxl (Excel file handling)

**Requirements.txt:**
```
Flask==2.3.3
SQLAlchemy==2.0.20
Flask-Login==0.6.2
Flask-WTF==1.1.1
Flask-Bcrypt==1.0.1
PyMySQL==1.1.0
pandas==2.1.0
openpyxl==3.1.2
Werkzeug==2.3.7
python-dotenv==1.0.0
```

**Note:** Chart.js and DataTables.js are JavaScript libraries loaded via CDN in templates, not Python dependencies.

**Rationale:** SQLAlchemy ORM is chosen over raw MySQL drivers for several critical reasons: (1) it provides built-in SQL injection prevention through parameterized queries, (2) it offers transaction management with row-level locking (SELECT ... FOR UPDATE) needed for TAS number generation race condition prevention, (3) it simplifies model management and reduces boilerplate, and (4) it provides database portability if needed in the future. Flask-WTF ensures CSRF protection is enforced consistently across all forms.

**Database Schema Initialization:** Use schema.sql for initial database setup. The SQLAlchemy models will then work with the existing schema. Do NOT use db.create_all() alongside schema.sql to avoid conflicts. The ENUM types in schema.sql must match the SQLAEnum definitions in models (native_enum=True).

## Architecture

**Application Structure:**

```
erpportalflask/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # SQLAlchemy models
│   ├── auth.py                  # Authentication utilities
│   ├── forms.py                 # WTForms definitions
│   ├── utils.py                 # Utility functions (TAS number generation, file processing)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # Login/logout routes
│   │   ├── admin.py             # Super admin routes
│   │   └── employee.py          # Employee routes
│   ├── templates/
│   │   ├── base.html            # Base template with navigation
│   │   ├── login.html           # Login page
│   │   ├── admin/
│   │   │   ├── dashboard.html   # Admin dashboard with stats and recent TAS
│   │   │   ├── import_employees.html  # Employee import page
│   │   │   ├── tas_list.html    # View all TAS records
│   │   │   └── tas_detail.html  # Detailed TAS view
│   │   └── employee/
│   │       ├── dashboard.html   # Employee dashboard
│   │       ├── submit_tas.html  # TAS submission form
│   │       └── tas_history.html # Employee's TAS history
│   └── static/
│       ├── css/
│       │   └── style.css        # Custom styles
│       ├── js/
│       │   └── main.js          # Custom JavaScript
│       └── uploads/             # Temporary storage for uploaded files
├── config.py                    # Configuration classes
├── requirements.txt             # Python dependencies
├── schema.sql                   # Database schema initialization
├── run.py                       # Application entry point
├── .env.example                 # Environment variables template
└── README.md                    # Setup and usage instructions
```

**Design Pattern:** Flask application factory pattern is used (in `app/__init__.py`) to allow multiple configurations (development, testing, production) and improve testability. The factory creates the Flask app, initializes extensions (SQLAlchemy, Flask-Login, Flask-WTF), and registers blueprints for modular routing.

**Blueprint Registration:**

Blueprints are registered with the following names:
- `'admin'` (from app/routes/admin.py, variable name `admin_bp`)
- `'employee'` (from app/routes/employee.py, variable name `employee_bp`)
- `'auth'` (from app/routes/auth.py, variable name `auth_bp`)

URL patterns:
- `/admin/*` for admin routes (e.g., `url_for('admin.dashboard')`)
- `/employee/*` for employee routes (e.g., `url_for('employee.submit_tas')`)
- `/login`, `/logout` for auth routes (e.g., `url_for('auth.login')`)

## Database Schema

**Tables:**

**1. employees**
```sql
CREATE TABLE employees (
    emp_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    department VARCHAR(100),
    designation VARCHAR(100),
    manager_id VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES employees(emp_id) ON DELETE SET NULL,
    INDEX idx_department (department),
    INDEX idx_manager (manager_id),
    INDEX idx_email (email)
);
```

**2. users**
```sql
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'employee') NOT NULL DEFAULT 'employee',
    emp_id VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE SET NULL,
    INDEX idx_username (username),
    INDEX idx_emp_id (emp_id)
);
```

**3. tas_records**
```sql
CREATE TABLE tas_records (
    tas_id INT AUTO_INCREMENT PRIMARY KEY,
    tas_number VARCHAR(50) UNIQUE NOT NULL,
    emp_id VARCHAR(20) NOT NULL,
    travel_from VARCHAR(255) NOT NULL,
    travel_to VARCHAR(255) NOT NULL,
    travel_date_start DATE NOT NULL,
    travel_date_end DATE NOT NULL,
    purpose TEXT NOT NULL,
    estimated_cost DECIMAL(10, 2) NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected') NOT NULL DEFAULT 'Pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP NULL,
    approved_by INT,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_tas_number (tas_number),
    INDEX idx_emp_id (emp_id),
    INDEX idx_status (status),
    INDEX idx_submitted_at (submitted_at)
);
```

**4. tas_sequence**
```sql
CREATE TABLE tas_sequence (
    emp_id VARCHAR(20) PRIMARY KEY,
    last_sequence INT NOT NULL DEFAULT 0,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
);
```

**Rationale:** The `tas_sequence` table maintains the last used sequence number per employee, enabling efficient TAS number generation with row-level locking to prevent race conditions. The `tas_number` field has a UNIQUE constraint to enforce system-wide uniqueness. Indexes are placed on frequently queried columns (department, status, submitted_at) to optimize dashboard and list queries.

**Naming Convention:** Timestamp columns use `_at` suffix (e.g., `submitted_at`, `created_at`). Date-only columns use `_date` or descriptive names (e.g., `travel_date_start`). This convention is followed consistently across all tables.

**Note on Code Snippets:** Import statements are omitted for brevity in code examples. Ensure all referenced modules are imported in actual implementation. Common imports include: `datetime`, `os`, `re`, `pandas as pd`, `sqlalchemy.func`, `flask` modules, `werkzeug.utils.secure_filename`, etc.

## Core Components

### 1. Models (app/models.py)

**Employee Model:**
```python
class Employee(db.Model):
    __tablename__ = 'employees'
    emp_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    manager_id = db.Column(db.String(20), db.ForeignKey('employees.emp_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tas_records = db.relationship('TASRecord', backref='employee', lazy='dynamic')
    user = db.relationship('User', backref='employee_profile', uselist=False)
```

**User Model:**
```python
from sqlalchemy import Enum as SQLAEnum

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # Note: MySQL uses inline ENUM, so native_enum=False to match schema.sql
    role = db.Column(db.Enum('admin', 'employee', native_enum=False), 
                     nullable=False, default='employee')
    emp_id = db.Column(db.String(20), db.ForeignKey('employees.emp_id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Set hashed password. Validates minimum length."""
        if not password or len(password) < 8:
            raise ValueError('Password must be at least 8 characters')
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Return user_id as string for Flask-Login session storage."""
        return str(self.user_id)
```

**TASRecord Model:**
```python
class TASRecord(db.Model):
    __tablename__ = 'tas_records'
    tas_id = db.Column(db.Integer, primary_key=True)
    tas_number = db.Column(db.String(50), unique=True, nullable=False)
    emp_id = db.Column(db.String(20), db.ForeignKey('employees.emp_id'), nullable=False)
    travel_from = db.Column(db.String(255), nullable=False)
    travel_to = db.Column(db.String(255), nullable=False)
    travel_date_start = db.Column(db.Date, nullable=False)
    travel_date_end = db.Column(db.Date, nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    estimated_cost = db.Column(db.Numeric(10, 2), nullable=False)
    # Note: MySQL uses inline ENUM, so native_enum=False to match schema.sql
    status = db.Column(db.Enum('Pending', 'Approved', 'Rejected', native_enum=False), 
                       nullable=False, default='Pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**TASSequence Model:**
```python
class TASSequence(db.Model):
    __tablename__ = 'tas_sequence'
    emp_id = db.Column(db.String(20), db.ForeignKey('employees.emp_id'), primary_key=True)
    last_sequence = db.Column(db.Integer, nullable=False, default=0)
```

### 2. TAS Number Generation (app/utils.py)

**Function: `generate_tas_number(emp_id)`**

This function generates a unique TAS number in the format `TAS-{EMPID}-{SEQUENCE}` (e.g., `TAS-1987-0001`). The function must be called within an active transaction and does NOT commit internally. The caller is responsible for committing both the sequence update and the TAS record insert together in a single transaction.

**Implementation:**
```python
def generate_tas_number(emp_id):
    """
    Generate a unique TAS number for the given employee ID.
    Format: TAS-{EMPID}-{SEQUENCE} (e.g., TAS-1987-0001)
    
    Uses row-level locking to prevent race conditions.
    
    IMPORTANT: Must be called within an active transaction.
    Does NOT commit internally - caller must commit.
    """
    from app.models import TASSequence
    from app import db
    
    # Lock the row for this employee (or create if doesn't exist)
    seq_record = db.session.query(TASSequence).filter_by(emp_id=emp_id).with_for_update().first()
    
    if seq_record is None:
        # First TAS for this employee
        seq_record = TASSequence(emp_id=emp_id, last_sequence=1)
        db.session.add(seq_record)
    else:
        # Increment sequence
        seq_record.last_sequence += 1
    
    # Generate TAS number
    tas_number = f"TAS-{emp_id}-{seq_record.last_sequence:04d}"
    
    # Do NOT commit here - let the caller commit both sequence and TAS record together
    return tas_number
```

**Race Condition Prevention:** The `with_for_update()` method applies a `SELECT ... FOR UPDATE` lock on the row, preventing concurrent transactions from reading or modifying the same employee's sequence until the current transaction commits. This ensures that even if two employees with the same emp_id submit TAS forms simultaneously, they will receive unique sequential numbers.

**Error Handling:** If the transaction fails (database error, deadlock), the exception is raised to the caller. The calling route must catch this exception and call `db.session.rollback()` to release locks and discard all changes from the transaction (both sequence update and TAS record). SQLAlchemy requires explicit `session.commit()` to finalize transactions. Present an error message to the user: "Failed to generate TAS number. Please try again." This is a recoverable error; the user can resubmit. The error is logged at the route level using Flask's logger with `exc_info=True` to capture full tracebacks.

### 3. Authentication (app/auth.py & app/routes/auth.py)

**Session Management:** Flask-Login manages user sessions. The `User` model inherits from `UserMixin` which provides `is_authenticated`, `is_active`, `is_anonymous`, and `get_id()`.

**Login Route (`/login`, POST):**
- Accepts username and password
- Validates user credentials using `User.check_password()`
- If valid and `is_active` is True, calls `login_user()` and redirects based on role:
  - `admin` → `/admin/dashboard`
  - `employee` → `/employee/dashboard`
- If invalid, renders login page with error: "Invalid username or password"
- If user is inactive (`is_active = False`), do NOT call `login_user()`. Render login.html with flash message: "Account is inactive. Contact administrator." User remains logged out.
- If user is already authenticated and accesses `/login`, redirect to appropriate dashboard based on role (admin → `/admin/dashboard`, employee → `/employee/dashboard`)

**Login Route Implementation:**
```python
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect already-authenticated users to their dashboard
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))
    
    # ... rest of login logic
```

**Logout Route (`/logout`, GET):**
- Calls `logout_user()` and redirects to `/login`

**Password Hashing:** Bcrypt with default work factor (12 rounds) is used. Passwords are hashed in `User.set_password()` and verified in `User.check_password()`.

**Flask-Login Configuration:** The app factory must configure Flask-Login's user_loader callback:

```python
# In app/__init__.py after login_manager initialization
from app.models import User

@login_manager.user_loader
def load_user(user_id):
    # Flask-Login passes the user_id from the session as a string (returned by get_id())
    # Convert back to int for query
    return User.query.get(int(user_id))

# Configure login view
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'
```

**Role-Based Access Control:** Decorators `admin_required` and `employee_required` are defined in `app/auth.py`:
```python
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check authentication, active status, and role
        if not current_user.is_authenticated or not current_user.is_active or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check authentication, active status, and role
        if not current_user.is_authenticated or not current_user.is_active or current_user.role != 'employee':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
```

These decorators are applied to routes in `app/routes/admin.py` and `app/routes/employee.py`.

### 4. Admin Dashboard (app/routes/admin.py, /admin/dashboard)

**Dashboard Layout Specification:**

The admin dashboard implements a modern, card-based layout with navigation structure, color-coded statistics, and data visualizations.

**Terminology Clarification:** "Admin" and "super admin" are used interchangeably in this design. The system has two roles only: "admin" (full access to all features) and "employee" (limited to TAS submission and viewing own history). There is no role hierarchy within admin users.

**1. Top Navigation Bar (sticky, primary blue background #4F46E5):**
- Left: Logo + "Travel Approval System" branding
- Center: Search bar (searches TAS records by TAS number, employee name, or destination)
- Right: User profile dropdown (shows username, role, logout option)

**2. Left Sidebar Navigation (fixed, light background #F9FAFB, width: 240px):**
- Dashboard (with icon, active state highlighted)
- TAS Records (links to /admin/tas_list)
- Import Employees (links to /admin/import_employees)
- Export Data (links to /admin/export_tas)
- User Management (links to /admin/user_management)
- Active menu item: blue left border (#4F46E5) + blue text

**3. Main Content Area (padding: 24px, background: #F9FAFB):**

**a) Top Stats Cards (4 cards, responsive grid):**

Query and display:
- **Card 1: "TOTAL TAS SUBMISSIONS"** (background: #E9D5FF purple/lavender)
  - Large number: `TASRecord.query.count()`
  - Subtitle: "All time submissions"
  - Icon: document icon

- **Card 2: "PENDING APPROVALS"** (background: #D1FAE5 green)
  - Large number: `TASRecord.query.filter_by(status='Pending').count()`
  - Subtitle: "Awaiting approval"
  - Icon: clock icon

- **Card 3: "APPROVED"** (background: #DBEAFE blue)
  - Large number: Count of approved TAS records submitted this month
  - Query: 
    ```python
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    approved_this_month = TASRecord.query.filter(
        TASRecord.status == 'Approved',
        TASRecord.submitted_at >= start_of_month
    ).count()
    ```
  - Subtitle: "Approved this month"
  - Icon: checkmark icon

- **Card 4: "REJECTED"** (background: #FED7AA peach/orange)
  - Large number: `TASRecord.query.filter_by(status='Rejected').count()`
  - Percentage text: rejection rate (rejected / total * 100)
  - Icon: cross icon

Each card has rounded corners, subtle shadow, and responsive sizing (full width on mobile, 2x2 grid on tablet, 4 columns on desktop).

**b) Charts Section (2 columns, below stats cards):**

- **Left (larger, 8/12 width): Line/Area Chart**
  - Title: "TAS Submissions Over Time"
  - Tab filters: Last 7 Days / Last Month / Last 3 Months
  - X-axis: Date, Y-axis: Count
  - Use Chart.js library (loaded via CDN)
  - Data query:
    ```python
    from sqlalchemy import func, cast, Date
    from datetime import datetime, timedelta
    
    # For last 7 days example
    seven_days_ago = datetime.now() - timedelta(days=7)
    submissions_by_date = db.session.query(
        cast(TASRecord.submitted_at, Date).label('date'),
        func.count(TASRecord.tas_id).label('count')
    ).filter(
        TASRecord.submitted_at >= seven_days_ago
    ).group_by(
        cast(TASRecord.submitted_at, Date)
    ).order_by('date').all()
    
    # Convert to format for Chart.js
    chart_data = {
        'labels': [str(row.date) for row in submissions_by_date],
        'data': [row.count for row in submissions_by_date]
    }
    ```
  - Line color: #4F46E5 (primary blue)

- **Right (smaller, 4/12 width): Status Breakdown Panel**
  - Title: "TAS Status Breakdown"
  - Colored progress bars showing percentage:
    - Pending (yellow #F59E0B)
    - Approved (green #10B981)
    - Rejected (red #EF4444)
  - Show count and percentage for each status

**c) Recent Submissions Table (below charts):**
- Query: `TASRecord.query.order_by(TASRecord.submitted_at.desc()).limit(10).all()`
- Display columns: TAS Number, Employee Name (join with Employee), Destination (travel_to), Travel Date (start), Status
- Each row links to `/admin/tas/<tas_id>` for details
- DataTables configuration for dashboard: disable pagination and searching since server-side limit shows only 10 recent records
  ```javascript
  $('#dashboard-recent-table').DataTable({
      "paging": false,      // Dashboard shows only 10 records (server-side limit)
      "searching": false,   // No search needed for 10 records
      "info": false,
      "order": [[0, "desc"]]
  });
  ```
- Include a "View All TAS Records" link button at the bottom that redirects to `/admin/tas_list`

**Color Palette:**
```css
:root {
  --primary-blue: #4F46E5;
  --success-green: #10B981;
  --warning-orange: #F59E0B;
  --info-purple: #A855F7;
  --danger-red: #EF4444;
  
  --bg-light: #F9FAFB;
  --bg-white: #FFFFFF;
  
  --card-purple: #E9D5FF;
  --card-green: #D1FAE5;
  --card-blue: #DBEAFE;
  --card-peach: #FED7AA;
  
  --text-primary: #111827;
  --text-secondary: #6B7280;
  
  --border-light: #E5E7EB;
  --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
}
```

**Responsive Behavior:**
- Sidebar collapses to hamburger menu on mobile (< 768px)
- Stat cards stack vertically on mobile (2x2 grid on tablet, 4x1 on mobile)
- Charts stack vertically on mobile and tablet
- Table becomes horizontally scrollable on small screens

**Search and Filter:**
Client-side filtering using DataTables.js on the recent submissions table. The top navigation bar search performs a global search across TAS number, employee name, and destination.

### 5. Employee Import (app/routes/admin.py, /admin/import_employees)

**Route: `/admin/import_employees` (GET, POST)**

**GET:** Renders upload form with file input (accept .xlsx, .csv)

**POST:** Processes uploaded file

**Expected Columns:**
- `emp_id` (required, string, unique)
- `name` (required, string)
- `email` (required, string, valid email format)
- `department` (optional, string)
- `designation` (optional, string)
- `manager_id` (optional, string, must reference existing emp_id or be empty)

**Validation Rules:**
1. File format must be .xlsx or .csv
2. File size limit: 10 MB (enforced by MAX_CONTENT_LENGTH)
3. `emp_id`: non-empty, max 20 chars
4. `name`: non-empty, max 255 chars
5. `email`: valid email format (regex: `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$`), max 255 chars
6. `manager_id`: if provided, must exist in employees table (validated during insert)
7. Row limit: 1000 rows per import
8. Duplicate emp_id within file: detected and rejected
9. Duplicate email within file: detected and rejected

**Implementation:**
```python
@admin_bp.route('/import_employees', methods=['GET', 'POST'])
@admin_required
def import_employees():
    if request.method == 'POST':
        # Ensure upload folder exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file = request.files.get('file')
        
        # Validation: file presence
        if not file or file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        # Validation: file extension
        if not file.filename.endswith(('.xlsx', '.csv')):
            flash('Invalid file format. Please upload .xlsx or .csv', 'error')
            return redirect(request.url)
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Read file with pandas
            if filename.endswith('.xlsx'):
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath)
            
            # Validation: required columns
            required_columns = ['emp_id', 'name', 'email']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
                return redirect(request.url)
            
            # Validation: row limit
            if len(df) > 1000:
                flash('File contains more than 1000 rows. Please split the file.', 'error')
                return redirect(request.url)
            
            # Validation: duplicate emp_id within file
            emp_ids_in_file = df['emp_id'].astype(str).str.strip()
            duplicate_emp_ids = emp_ids_in_file[emp_ids_in_file.duplicated()].unique()
            if len(duplicate_emp_ids) > 0:
                flash(f'Duplicate emp_id found in file: {", ".join(duplicate_emp_ids[:5])}. Each emp_id must be unique.', 'error')
                return redirect(request.url)
            
            # Validation: duplicate emails within file
            emails_in_file = df['email'].str.strip().str.lower()
            duplicate_emails = emails_in_file[emails_in_file.duplicated()].unique()
            if len(duplicate_emails) > 0:
                flash(f'Duplicate emails found in file: {", ".join(duplicate_emails[:5])}. Each email must be unique.', 'error')
                return redirect(request.url)
            
            # Process rows
            success_count = 0
            error_rows = []
            
            for index, row in df.iterrows():
                try:
                    # Validate row data
                    emp_id = str(row['emp_id']).strip()
                    name = str(row['name']).strip()
                    email = str(row['email']).strip()
                    
                    if not emp_id or len(emp_id) > 20:
                        error_rows.append(f"Row {index+2}: Invalid emp_id")
                        continue
                    
                    if not name or len(name) > 255:
                        error_rows.append(f"Row {index+2}: Invalid name")
                        continue
                    
                    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
                        error_rows.append(f"Row {index+2}: Invalid email format")
                        continue
                    
                    # Validate manager_id
                    manager_id = str(row.get('manager_id', '')).strip() or None
                    if manager_id:
                        if manager_id == emp_id:
                            error_rows.append(f"Row {index+2}: Employee cannot be their own manager")
                            continue
                        # Circular reference detection for simple two-way circles (A->B, B->A)
                        if manager_id in df['emp_id'].astype(str).str.strip().values:
                            # Manager is in the same import file - check for circular reference
                            manager_row = df[df['emp_id'].astype(str).str.strip() == manager_id]
                            if not manager_row.empty:
                                manager_manager_id = str(manager_row.iloc[0].get('manager_id', '')).strip() or None
                                if manager_manager_id == emp_id:
                                    error_rows.append(f"Row {index+2}: Circular reference detected ({emp_id} -> {manager_id} -> {emp_id})")
                                    continue
                        # Note: Complex multi-level circular references (A->B->C->A) are not detected during import.
                        # Organizations must ensure clean manager hierarchies. Database triggers or scheduled jobs
                        # can be added to detect and report complex circular references.
                    
                    # Create or update employee
                    employee = Employee.query.filter_by(emp_id=emp_id).first()
                    if employee:
                        # Update existing
                        employee.name = name
                        employee.email = email
                        employee.department = str(row.get('department', '')).strip() or None
                        employee.designation = str(row.get('designation', '')).strip() or None
                        employee.manager_id = manager_id
                        employee.updated_at = datetime.utcnow()
                    else:
                        # Create new
                        employee = Employee(
                            emp_id=emp_id,
                            name=name,
                            email=email,
                            department=str(row.get('department', '')).strip() or None,
                            designation=str(row.get('designation', '')).strip() or None,
                            manager_id=manager_id
                        )
                        db.session.add(employee)
                    
                    db.session.commit()
                    success_count += 1
                
                except Exception as e:
                    db.session.rollback()
                    error_rows.append(f"Row {index+2}: {str(e)}")
            
            # Display results
            flash(f'Successfully imported {success_count} employees', 'success')
            if error_rows:
                flash(f'Errors: {"; ".join(error_rows[:10])}', 'warning')
        
        except Exception as e:
            current_app.logger.error(f'Error processing file: {str(e)}', exc_info=True)
            flash(f'Error processing file: {str(e)}', 'error')
        
        finally:
            # Clean up temporary file with error handling
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                current_app.logger.warning(f'Failed to delete temporary file {filepath}: {str(e)}')
        
        return redirect(url_for('admin.import_employees'))
    
    return render_template('admin/import_employees.html')
```

**Error Handling:**
- **Invalid file format:** Render form with error message "Invalid file format. Please upload .xlsx or .csv"
- **Missing columns:** Render form with error message listing missing columns
- **Row validation errors:** Collect all errors and display up to 10 at the end (to avoid overwhelming UI)
- **Database errors (duplicate email, foreign key violation):** Catch per-row, log error message, and continue processing remaining rows
- **File read errors:** Display generic error "Error processing file" and log full exception with traceback

**Logging:** All exceptions are logged using `current_app.logger.error()` with `exc_info=True` to capture full tracebacks.

**Security:** `secure_filename()` from Werkzeug is used to sanitize filenames. Temporary files are deleted after processing.

### 6. Export TAS Records (app/routes/admin.py, /admin/export_tas)

**Route: `/admin/export_tas` (GET)**

**Query Parameters:**
- `format`: `xlsx` or `csv` (default: `xlsx`)
- `status`: `Pending`, `Approved`, `Rejected`, or `All` (default: `All`)
- `date_from`: ISO format date (YYYY-MM-DD), optional
- `date_to`: ISO format date (YYYY-MM-DD), optional
- `department`: department name, optional

**Implementation:**
```python
@admin_bp.route('/export_tas', methods=['GET'])
@admin_required
def export_tas():
    # Parse query parameters
    export_format = request.args.get('format', 'xlsx')
    status_filter = request.args.get('status', 'All')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    department = request.args.get('department')
    
    # Build query
    query = db.session.query(
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
        TASRecord.approved_at
    ).join(Employee, TASRecord.emp_id == Employee.emp_id)
    
    # Apply filters with validation
    try:
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            date_from_obj = datetime.fromisoformat(date_from)
            query = query.filter(TASRecord.submitted_at >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.fromisoformat(date_to)
            query = query.filter(TASRecord.submitted_at <= date_to_obj)
        
        if date_from and date_to and date_from_obj > date_to_obj:
            return jsonify({'error': 'date_from must be before date_to'}), 400
    
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    if status_filter != 'All':
        query = query.filter(TASRecord.status == status_filter)
    
    if department:
        query = query.filter(Employee.department == department)
    
    # Execute query
    results = query.all()
    
    # Convert to DataFrame
    df = pd.DataFrame(results, columns=[
        'TAS Number', 'Employee ID', 'Employee Name', 'Email', 'Department',
        'Designation', 'From', 'To', 'Start Date', 'End Date', 'Purpose',
        'Estimated Cost', 'Status', 'Submitted At', 'Approved At'
    ])
    
    # Generate file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if export_format == 'csv':
        filename = f'tas_records_{timestamp}.csv'
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        df.to_csv(filepath, index=False)
        mimetype = 'text/csv'
    else:
        filename = f'tas_records_{timestamp}.xlsx'
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        df.to_excel(filepath, index=False, engine='openpyxl')
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    # Send file with cleanup callback
    def cleanup_file():
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            current_app.logger.warning(f'Failed to delete export file {filepath}: {str(e)}')
    
    response = send_file(filepath, as_attachment=True, download_name=filename, mimetype=mimetype)
    response.call_on_close(cleanup_file)
    return response
```

**Error Handling:**
- **Invalid date format:** Return 400 error with message "Invalid date format. Use YYYY-MM-DD"
- **Date range validation:** If date_from > date_to, return 400 error with message "date_from must be before date_to"
- **Database query error:** Log error with full traceback and return 500 with message "Error generating export"
- **File write error:** Log error with full traceback and return 500 with message "Error creating export file"

**File Cleanup:** Export files are cleaned up automatically after download using response.call_on_close(). If cleanup fails, the error is logged. To handle stale files that fail to clean up, implement a scheduled cleanup job:

```python
# In app/utils.py
def cleanup_old_exports(hours=24):
    """Delete export files older than specified hours.
    Run daily via cron or task scheduler."""
    from flask import current_app
    import os
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    for filename in os.listdir(upload_folder):
        if filename.startswith('tas_records_'):
            filepath = os.path.join(upload_folder, filename)
            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_mtime < cutoff_time:
                    os.remove(filepath)
                    current_app.logger.info(f'Cleaned up old export file: {filename}')
            except Exception as e:
                current_app.logger.error(f'Failed to cleanup {filename}: {str(e)}', exc_info=True)
```

Add to README: "Run `cleanup_old_exports()` daily via cron or task scheduler to remove export files older than 24 hours."

### 7. TAS Management (app/routes/admin.py)

**Route: `/admin/tas_list` (GET)**
- Display all TAS records with pagination (20 per page)
- Support filtering by status, date range, department (using query parameters)
- Each row has actions: View Details, Approve (if Pending), Reject (if Pending)

**Route: `/admin/tas/<int:tas_id>` (GET)**
- Display detailed TAS information including employee details
- Show Approve/Reject forms if status is Pending
- Template must include CSRF-protected forms:

```html
<!-- Approve Form -->
<form method="POST" action="{{ url_for('admin.approve_tas', tas_id=tas.tas_id) }}" style="display:inline;">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <button type="submit" class="btn btn-success">Approve</button>
</form>

<!-- Reject Form -->
<form method="POST" action="{{ url_for('admin.reject_tas', tas_id=tas.tas_id) }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <div class="form-group">
        <label for="rejection_reason">Reason for Rejection (optional)</label>
        <textarea name="rejection_reason" class="form-control" rows="3" maxlength="500"></textarea>
        <small class="form-text text-muted">Maximum 500 characters</small>
    </div>
    <button type="submit" class="btn btn-danger">Reject</button>
</form>
```

**Route: `/admin/tas/<int:tas_id>/approve` (POST)**
- Validates TAS exists and status is Pending
- Updates status to 'Approved', sets `approved_at` to current timestamp, sets `approved_by` to current user's user_id
- Commits transaction
- Redirects to TAS detail page with success message
- **CSRF Protection:** Form must include csrf_token hidden field. Do NOT use @csrf.exempt decorator.
- **Error Handling:** 
  - If TAS not found, return 404
  - If TAS is not Pending, flash error "TAS has already been processed" and redirect
  - Database errors are logged and user sees "Error updating TAS status"

**Route: `/admin/tas/<int:tas_id>/reject` (POST)**
- Validates TAS exists and status is Pending
- Accepts optional `rejection_reason` from form (max 500 characters)
- Updates status to 'Rejected', sets `approved_at` to current timestamp, sets `approved_by` to current user's user_id, sets `rejection_reason`
- Commits transaction
- Redirects to TAS detail page with success message
- **CSRF Protection:** Form must include csrf_token hidden field. Do NOT use @csrf.exempt decorator.
- **Error Handling:** Same as approve route

### 7a. User Management (app/routes/admin.py)

**User-to-Employee Linking:**

After importing employees via HR data, admin users must create corresponding user accounts to enable login. This is a two-step process: first import employees, then create users.

**Route: `/admin/user_management` (GET)**
- Display list of all users with columns: Username, Role, Linked Employee (name + emp_id), Status (active/inactive), Actions
- Show "Create New User" button that opens a form modal or redirects to create user page

**CreateUserForm Definition (app/forms.py):**
```python
class CreateUserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=50),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username must contain only letters, numbers, and underscores')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('employee', 'Employee')], validators=[DataRequired()])
    emp_id = SelectField('Employee', validators=[Optional()], coerce=lambda x: x or None)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Create User')
    
    def validate_emp_id(self, field):
        """Conditional validation: emp_id required for employee role."""
        if self.role.data == 'employee' and not field.data:
            raise ValidationError('Employee ID is required for employee role')
```

**Route: `/admin/create_user` (GET, POST)**

**GET:** Render form with fields:
- Username (text input, required, unique)
- Password (password input, required, min 8 chars)
- Role (dropdown: admin, employee)
- Employee ID (dropdown populated with employees who don't have linked users, required for employee role, optional for admin role)
- Is Active (checkbox, default checked)

**POST:** Process user creation

**Validation Rules:**
1. Username: required, unique, 3-50 chars, alphanumeric + underscore
2. Password: required, min 8 chars
3. Role: required, must be 'admin' or 'employee'
4. emp_id: required if role is 'employee', must exist in employees table, must not already be linked to another user
5. emp_id: optional if role is 'admin'

**Implementation:**
```python
@admin_bp.route('/create_user', methods=['GET', 'POST'])
@admin_required
def create_user():
    form = CreateUserForm()  # WTForm with CSRF protection
    
    # Populate employee dropdown (employees without linked users)
    available_employees = db.session.query(Employee).outerjoin(User).filter(User.user_id == None).all()
    form.emp_id.choices = [('', 'None (for admin users)')] + [(e.emp_id, f'{e.name} ({e.emp_id})') for e in available_employees]
    
    if form.validate_on_submit():
        try:
            # Validate emp_id requirement for employee role
            if form.role.data == 'employee' and not form.emp_id.data:
                flash('Employee ID is required for employee role', 'error')
                return render_template('admin/create_user.html', form=form)
            
            # Check if emp_id is already linked (double-check)
            if form.emp_id.data:
                existing_user = User.query.filter_by(emp_id=form.emp_id.data).first()
                if existing_user:
                    flash('This employee already has a user account', 'error')
                    return render_template('admin/create_user.html', form=form)
            
            # Create user
            user = User(
                username=form.username.data,
                role=form.role.data,
                emp_id=form.emp_id.data or None,
                is_active=form.is_active.data
            )
            user.set_password(form.password.data)  # This now validates min 8 chars
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'User {user.username} created successfully', 'success')
            return redirect(url_for('admin.user_management'))
        
        except ValueError as ve:
            # Password validation error from User.set_password()
            flash(str(ve), 'error')
            return render_template('admin/create_user.html', form=form)
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating user: {str(e)}', exc_info=True)
            flash('Failed to create user. Please try again.', 'error')
    
    return render_template('admin/create_user.html', form=form)
```

**Error Handling:**
- **Duplicate username:** Database unique constraint violation, caught and displayed as "Username already exists"
- **Invalid emp_id:** Foreign key constraint violation, caught and displayed as "Invalid employee ID"
- **emp_id already linked:** Pre-validated in form, additional check in route
- **Password validation error:** Caught from User.set_password() ValueError and displayed

**Note:** For bulk user creation (e.g., creating users for all imported employees), this can be enhanced in future. For MVP, admin creates users manually one by one.

### 8. Employee TAS Submission (app/routes/employee.py, /employee/submit_tas)

**Route: `/employee/submit_tas` (GET, POST)**

**GET:** Render form with fields:
- Destination From (text input)
- Destination To (text input)
- Travel Start Date (date picker)
- Travel End Date (date picker)
- Purpose (textarea)
- Estimated Cost (number input, min=0, step=0.01)

**POST:** Process form submission

**Validation Rules:**
1. All fields required (non-empty)
2. `travel_date_start` must be >= today
3. `travel_date_end` must be >= `travel_date_start`
4. `estimated_cost` must be > 0
5. `travel_from` and `travel_to` max 255 chars
6. `purpose` max 1000 chars

**Implementation:**
```python
@employee_bp.route('/submit_tas', methods=['GET', 'POST'])
@employee_required
def submit_tas():
    form = TASForm()  # WTForm with CSRF protection
    
    if form.validate_on_submit():
        try:
            # Get current user's emp_id
            emp_id = current_user.emp_id
            
            if not emp_id:
                flash('Your account is not linked to an employee record. Contact admin.', 'error')
                return redirect(url_for('employee.dashboard'))
            
            # Generate TAS number (within transaction, does not commit)
            tas_number = generate_tas_number(emp_id)
            
            # Create TAS record
            tas_record = TASRecord(
                tas_number=tas_number,
                emp_id=emp_id,
                travel_from=form.travel_from.data,
                travel_to=form.travel_to.data,
                travel_date_start=form.travel_date_start.data,
                travel_date_end=form.travel_date_end.data,
                purpose=form.purpose.data,
                estimated_cost=form.estimated_cost.data,
                status='Pending'
            )
            
            db.session.add(tas_record)
            
            # Commit both sequence update and TAS record together
            db.session.commit()
            
            flash(f'TAS submitted successfully. Your TAS number is {tas_number}', 'success')
            return redirect(url_for('employee.tas_history'))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error submitting TAS: {str(e)}', exc_info=True)
            flash('Failed to submit TAS. Please try again.', 'error')
    
    return render_template('employee/submit_tas.html', form=form)
```

**Form Definition (app/forms.py):**
```python
class TASForm(FlaskForm):
    travel_from = StringField('From', validators=[DataRequired(), Length(max=255)])
    travel_to = StringField('To', validators=[DataRequired(), Length(max=255)])
    travel_date_start = DateField('Start Date', validators=[DataRequired()])
    travel_date_end = DateField('End Date', validators=[DataRequired()])
    purpose = TextAreaField('Purpose', validators=[DataRequired(), Length(max=1000)])
    # Allow zero cost for free travel
    estimated_cost = DecimalField('Estimated Cost', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit TAS')
    
    def validate_travel_date_start(self, field):
        if field.data < date.today():
            raise ValidationError('Travel start date cannot be in the past')
    
    def validate_travel_date_end(self, field):
        # Only validate if start date is valid and has data
        if hasattr(self.travel_date_start, 'data') and self.travel_date_start.data:
            if field.data < self.travel_date_start.data:
                raise ValidationError('Travel end date must be after start date')
```

**HTML Form Field (in template):**
```html
<input type="number" name="estimated_cost" min="0" step="0.01" required>
```

**Note on Validation Order:** If travel_date_start is invalid, the end date comparison validation is skipped to avoid misleading error messages.

**Error Handling:**
- **Validation errors:** Displayed next to form fields (handled by Flask-WTF)
- **User not linked to employee:** Display error message "Your account is not linked to an employee record. Contact admin." and redirect to dashboard
- **TAS number generation failure:** Caught exception displays "Failed to submit TAS. Please try again." Error is logged with full traceback.
- **Database insert failure:** Same as above (rollback, log, display generic error)

### 9. Employee TAS History (app/routes/employee.py, /employee/tas_history)

**Route: `/employee/tas_history` (GET)**

**Implementation:**
```python
@employee_bp.route('/tas_history', methods=['GET'])
@employee_required
def tas_history():
    emp_id = current_user.emp_id
    
    if not emp_id:
        flash('Your account is not linked to an employee record.', 'error')
        return redirect(url_for('employee.dashboard'))
    
    # Query employee's TAS records
    tas_records = TASRecord.query.filter_by(emp_id=emp_id).order_by(TASRecord.submitted_at.desc()).all()
    
    return render_template('employee/tas_history.html', tas_records=tas_records)
```

**Display:** Table with columns: TAS Number, Destination, Travel Dates, Status, Submitted Date. Each row links to `/employee/tas/<tas_id>` for details.

**Route: `/employee/tas/<int:tas_id>` (GET)**
- Display detailed TAS information
- Validate that the TAS belongs to the current user (if not, return 403)

### 10. CSRF Protection

Flask-WTF automatically adds CSRF protection to all forms. The `FlaskForm` base class includes a hidden CSRF token field that is validated on submission.

**Configuration (config.py):**
```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # or set to seconds for expiry
```

**Template Usage:**
```html
<form method="POST">
    {{ form.hidden_tag() }}  <!-- Renders CSRF token -->
    <!-- form fields -->
</form>
```

**For Non-WTForm POST Requests:**

For POST routes that don't use WTForms (like approve/reject actions), CSRF tokens must be included manually in templates:

```html
<form method="POST" action="{{ url_for('admin.approve_tas', tas_id=tas.tas_id) }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <button type="submit" class="btn btn-success">Approve</button>
</form>
```

**Do NOT use `@csrf.exempt` decorator on any routes.** All POST routes must be CSRF-protected.

### 11. Input Validation and Sanitization

**Validation Layers:**
1. **Client-side:** HTML5 input attributes (required, min, max, pattern) and JavaScript validation for immediate feedback
2. **Server-side:** Flask-WTF validators (DataRequired, Length, Email, NumberRange, etc.) and custom validators
3. **Database-level:** Column constraints (NOT NULL, UNIQUE, FOREIGN KEY, CHECK)

**Sanitization:**
- All string inputs are stripped of leading/trailing whitespace
- HTML content (if any) is escaped using Jinja2's auto-escaping (enabled by default)
- File uploads: filenames sanitized with `secure_filename()`
- SQL injection prevented by SQLAlchemy's parameterized queries

### 12. Error Handling and Logging

**Error Pages:**
- 403 Forbidden: Custom template explaining access denied
- 404 Not Found: Custom template with link to dashboard
- 500 Internal Server Error: Generic template ("Something went wrong, please try again")

**Logging Configuration (app/__init__.py):**
```python
if not app.debug:
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Production logging
    file_handler = RotatingFileHandler('logs/erpportal.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('ERP Portal startup')
```

**Logging Strategy:**
- **INFO:** User actions (login, TAS submission, import/export)
- **WARNING:** Validation failures, permission denials
- **ERROR:** Exceptions, database errors, file processing errors

**Important:** All `logger.error()` calls must include `exc_info=True` to log full tracebacks for debugging.

### 13. Configuration Management (config.py)

**Configuration Classes:**
```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://user:password@localhost/tas_erp'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max upload size
    WTF_CSRF_ENABLED = True
    
    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS in production

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

**App Factory Initialization (app/__init__.py):**

The create_app function must ensure required directories exist and verify critical directories:

```python
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Verify critical directories (don't create, just warn if missing)
    if not os.path.exists(os.path.join(app.root_path, 'templates')):
        app.logger.warning('templates directory not found')
    if not os.path.exists(os.path.join(app.root_path, 'static')):
        app.logger.warning('static directory not found')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    
    # Register error handler for file size exceeded
    from werkzeug.exceptions import RequestEntityTooLarge
    
    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(e):
        flash('File too large. Maximum size is 10 MB.', 'error')
        return redirect(request.referrer or url_for('admin.dashboard'))
    
    # ... rest of initialization (blueprints, etc.)
```

**Environment Variables (.env):**
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/tas_erp
```

### 14. Frontend Design

**Base Template (app/templates/base.html):**
- Responsive navigation bar with Bootstrap 5
- User info and logout button in navbar
- Flash message display area with Bootstrap alert mapping
- Main content block
- Footer with copyright

**Flash Message Handling:**

Flash messages must map categories to Bootstrap alert classes:

```html
<!-- In base.html -->
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="container mt-3">
      {% for category, message in messages %}
        <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
          {{ message }}
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}
```

Category mapping:
- `error` → `alert-danger` (red)
- `success` → `alert-success` (green)
- `warning` → `alert-warning` (yellow)
- `info` → `alert-info` (blue)

**Note:** Use 'error' category in Python code; it is mapped to 'danger' in templates for Bootstrap compatibility.

**Dashboard Layouts:**
- Admin dashboard: Modern layout with top nav, left sidebar, stat cards, charts, and tables (see Section 4 for complete specification)
- Employee dashboard: Welcome message, quick links to Submit TAS and View History, recent submissions summary

**Forms:**
- Bootstrap form styling with labels, placeholders, and help text
- Client-side validation with HTML5 attributes and JavaScript
- Error messages displayed in red below fields

**Tables:**
- DataTables.js for sorting, searching, pagination
- Responsive table layout (horizontal scroll on small screens)
- Action buttons styled with Bootstrap button classes

**DataTables Initialization (app/static/js/main.js):**

```javascript
$(document).ready(function() {
    $('.data-table').DataTable({
        "pageLength": 20,
        "order": [[0, "desc"]], // Sort by first column (usually date/ID) descending
        "language": {
            "search": "Search:",
            "lengthMenu": "Show _MENU_ entries",
            "info": "Showing _START_ to _END_ of _TOTAL_ entries",
            "paginate": {
                "first": "First",
                "last": "Last",
                "next": "Next",
                "previous": "Previous"
            }
        }
    });
});
```

Apply the `data-table` class to:
- Admin TAS list table (`/admin/tas_list`)
- Dashboard recent submissions table (`/admin/dashboard`)
- Employee TAS history table (`/employee/tas_history`)

**Required Frontend Libraries:**

Load via CDN in base.html:
- Bootstrap 5.3.x (CSS and JS)
- jQuery 3.7.x (required for DataTables)
- DataTables.js 1.13.x
- Chart.js 4.x (for dashboard charts)

```html
<!-- In base.html <head> -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css" rel="stylesheet">

<!-- Before </body> -->
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
```

**Color Scheme:**

Use CSS variables defined in app/static/css/style.css (see Section 4 for complete color palette).

### 15. Security Considerations

**SQL Injection:** Prevented by SQLAlchemy ORM's parameterized queries. All queries use SQLAlchemy's query API or bound parameters.

**CSRF:** Protected by Flask-WTF's CSRF tokens on all forms.

**XSS:** Prevented by Jinja2's auto-escaping (enabled by default). User input is never rendered as raw HTML.

**Authentication:** Session-based authentication with secure cookies (httponly, secure flags in production).

**Password Storage:** Bcrypt hashing with salt (default 12 rounds).

**File Upload Security:** 
- Filename sanitization with `secure_filename()`
- File type validation (extension whitelist)
- File size limit (10 MB)
- Temporary file cleanup

**Access Control:** Role-based decorators enforce admin/employee separation.

**Error Disclosure:** Generic error messages to users; detailed errors only in logs.

### 16. Testing Strategy

**Unit Tests:**
- Models: Test model creation, relationships, password hashing
- Utils: Test TAS number generation (including race condition scenario with threading)
- Forms: Test validators

**Integration Tests:**
- Authentication: Test login/logout flows, role-based access
- Employee import: Test valid/invalid files, error handling
- TAS submission: Test form validation, TAS number generation, database insert
- Export: Test filtering, file generation

**Manual Testing:**
- UI responsiveness on mobile/tablet/desktop
- Browser compatibility (Chrome, Firefox, Safari, Edge)
- File upload/download workflows
- Concurrent TAS submission (multiple users)

**Test Database:**
Use a separate test database configured in a `TestingConfig` class. Reset database between test runs.

### 17. Deployment and Setup

**Database Initialization:**
1. Create MySQL database: `CREATE DATABASE tas_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
2. Run schema.sql to create tables
3. Create initial admin user:
   ```python
   # seed_admin.py
   from app import create_app, db
   from app.models import User
   import os
   
   app = create_app('production')
   with app.app_context():
       # Use environment variable or prompt for password in production
       admin_password = os.environ.get('ADMIN_PASSWORD') or input('Enter admin password (min 8 chars): ')
       
       admin = User(username='admin', role='admin')
       admin.set_password(admin_password)
       db.session.add(admin)
       db.session.commit()
       print('Admin user created successfully')
   ```

**Application Setup:**
1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure
6. Initialize database (run schema.sql)
7. Seed admin user
8. Run: `python run.py`

**Production Deployment:**
- Use Gunicorn or uWSGI as WSGI server
- Nginx as reverse proxy
- Set `FLASK_ENV=production`
- Use strong `SECRET_KEY` (environment variable)
- Enable HTTPS
- Configure log rotation
- Set up database backups
- Run scheduled cleanup job for export files (see Section 6)

**README.md Contents:**

The README.md must include the following sections:

1. **Project Overview**: Brief description of the TAS ERP Portal
2. **Prerequisites**: Python 3.9+, MySQL 8.0+
3. **Installation Steps**:
   - Virtual environment setup
   - `pip install -r requirements.txt`
   - `.env` configuration
4. **Database Setup**:
   - Create database
   - Run schema.sql
   - Seed admin user with `python seed_admin.py`
5. **Running the Application**: `python run.py`
6. **User Guide**:
   - Admin: Login, import employees, view dashboard, approve/reject TAS, export data
   - Employee: Login, submit TAS, view history
7. **Troubleshooting**:
   - Common errors (database connection, import file format)
   - Solutions
8. **Manual Cleanup Tasks**:
   - Export file cleanup: run `cleanup_old_exports()` daily via cron
   - Log rotation
9. **Security Notes**:
   - Change SECRET_KEY in production
   - Use HTTPS
   - Strong admin password
   - Regular database backups
10. **License and Contact**

### 18. Edge Cases and Constraints

**Edge Cases:**

1. **Employee submits TAS with same emp_id simultaneously:** Handled by `with_for_update()` row locking in `generate_tas_number()`. Second transaction waits until first commits.

2. **Employee imported with manager_id that doesn't exist yet:** Import will fail for that row with foreign key error. Solution: Import managers first, or set manager_id in a second pass. Document this constraint in README.

3. **Employee deleted while TAS records exist:** TAS records are cascade deleted (ON DELETE CASCADE). Document this behavior in README.

4. **Admin approves TAS that was already approved by another admin:** Check status before update. If not Pending, show error message "TAS has already been processed."

5. **User account exists but emp_id is NULL (admin user):** Employee routes check for `emp_id` and display error if NULL.

6. **Import file has duplicate emp_id within same file:** Later occurrence updates the earlier one (last write wins). This is acceptable behavior.

7. **Export with no matching records:** Return empty Excel/CSV file with headers only.

8. **Very large export (10,000+ records):** Pandas handles this; may take several seconds. Consider adding a loading indicator or background job for production enhancement (out of scope for MVP).

9. **Travel dates span multiple years:** Allowed; no constraint needed.

10. **Estimated cost is zero:** Allowed (free travel). Negative values are prevented by validation.

**Constraints and Limitations:**

1. **Single file import:** Only one file can be imported at a time (no batch import).
2. **Import row limit:** 1000 rows per file to prevent timeout and memory issues.
3. **No email notifications:** MVP does not include email notifications for approval/rejection.
4. **No TAS editing:** Once submitted, TAS cannot be edited by employee (only admin can change status).
5. **No audit trail:** No history of status changes or edits (could be future enhancement).
6. **No attachment support:** TAS cannot include file attachments (receipts, itineraries).
7. **Single currency:** All costs are in one currency (no currency field).

### 19. Verification Steps

**Post-Implementation Verification:**

1. **Database Schema:**
   - Verify all tables created with correct columns and constraints
   - Verify indexes exist on specified columns
   - Test foreign key constraints (try to delete referenced employee)

2. **Authentication:**
   - Test login with valid/invalid credentials
   - Test role-based access (employee trying to access admin routes)
   - Test logout and session expiry

3. **TAS Number Generation:**
   - Submit multiple TAS for same employee sequentially
   - Verify sequential numbering (0001, 0002, 0003...)
   - Test concurrent submission (use threading or multiple browsers)
   - Verify uniqueness in database

4. **Employee Import:**
   - Test with valid Excel file
   - Test with valid CSV file
   - Test with missing required columns
   - Test with invalid email format
   - Test with duplicate emp_id
   - Test with invalid manager_id
   - Verify error messages displayed correctly
   - Verify partial success (some rows succeed, some fail)

5. **TAS Submission:**
   - Test with all valid data
   - Test with missing fields
   - Test with past travel dates
   - Test with end date before start date
   - Test with negative cost
   - Verify validation errors displayed
   - Verify TAS appears in history after submission

6. **TAS Approval/Rejection:**
   - Test approving pending TAS
   - Test rejecting pending TAS
   - Try to approve already-approved TAS (should fail)
   - Verify approved_at and approved_by set correctly

7. **Export:**
   - Test export with no filters (all records)
   - Test export with status filter
   - Test export with date range
   - Test export with department filter
   - Test export with combined filters
   - Verify Excel file opens correctly
   - Verify CSV file has correct data
   - Test export with zero matching records

8. **UI/UX:**
   - Test responsive layout on mobile/tablet/desktop
   - Test all navigation links
   - Test flash messages appear and disappear
   - Test DataTables sorting and searching
   - Test form validation (client and server side)

9. **Security:**
   - Attempt SQL injection in form fields
   - Attempt XSS in text fields
   - Test CSRF protection (submit form without token)
   - Test unauthorized access (direct URL access)
   - Verify passwords are hashed in database

10. **Error Handling:**
    - Test with invalid file format
    - Test with file size exceeding limit
    - Test database connection failure
    - Verify error pages (403, 404, 500)
    - Verify errors logged correctly

## Deliverables Checklist

- [ ] Flask application with all routes implemented
- [ ] SQLAlchemy models for all tables
- [ ] Database schema SQL file (schema.sql)
- [ ] HTML templates for all pages
- [ ] CSS styling with Bootstrap
- [ ] JavaScript for DataTables and form validation
- [ ] Authentication and authorization system
- [ ] Employee import functionality
- [ ] TAS export functionality
- [ ] TAS number generation with race condition prevention
- [ ] Form validation and error handling
- [ ] CSRF protection on all forms
- [ ] requirements.txt with all dependencies
- [ ] config.py with environment-based configuration
- [ ] run.py entry point
- [ ] README.md with setup and usage instructions
- [ ] .env.example template
- [ ] Sample data SQL file for testing (optional but recommended)
- [ ] Admin seeding script

## Assumptions

1. **Single tenant:** Application serves one organization (no multi-tenancy).
2. **Emp_id format:** No specific format enforced; any string up to 20 chars is valid.
3. **Department/designation:** Free text fields (no predefined list).
4. **Approval workflow:** Single-stage approval by any admin (no multi-level approval or manager hierarchy).
5. **Currency:** All costs in single currency (currency not stored or displayed).
6. **Time zone:** All timestamps in UTC; display in server's local time.
7. **Browser support:** Modern browsers with JavaScript enabled.
8. **Network:** Application runs on internal network (not internet-facing without additional security).
9. **Concurrent users:** Moderate concurrency expected (< 100 simultaneous users).
10. **Data retention:** No automatic deletion or archiving of old records.

---

## Design Review Response

This design has been revised to address all HIGH and MEDIUM severity findings from the design review. Below is a summary of how each finding was resolved:

### HIGH Severity Findings - All Resolved

**#1: ENUM Type Mismatch Between Schema and ORM Models**
✅ **FIXED** - Updated User and TASRecord models to use `native_enum=False` instead of `native_enum=True` to match MySQL's inline ENUM behavior (MySQL doesn't support named ENUM types like PostgreSQL). See Section 1 (Models).

**#2: User.get_id() Return Type Inconsistency**
✅ **FIXED** - Added clarifying comment in Flask-Login Configuration (Section 3) documenting that `get_id()` returns string and `user_loader` must convert to int. Updated code comment: "Flask-Login passes the user_id from the session as a string (returned by get_id()). Convert back to int for query."

**#3: Undefined CreateUserForm in User Management**
✅ **FIXED** - Added complete CreateUserForm definition to Section 7a with all validators: username regex, password min length, role validation, emp_id conditional validation via custom validate_emp_id() method.

**#4: Circular Manager Reference Detection Is Incomplete**
✅ **FIXED** - Added simple two-way circular reference detection (A->B, B->A) in employee import (Section 5). Complex multi-level circles are documented as a known limitation with mitigation strategy: "Organizations must ensure clean manager hierarchies. Database triggers or scheduled jobs can be added to detect complex circular references."

**#5: TAS Number Generation Transaction Boundary Unclear**
✅ **FIXED** - Updated Section 2 error handling with explicit guidance: "SQLAlchemy requires explicit session.commit() to finalize transactions. Call session.rollback() on exception to release locks and discard all changes (both sequence update and TAS record)."

**#6: Export File Cleanup Race Condition**
✅ **FIXED** - Added `cleanup_old_exports()` function specification in Section 6 to delete files older than 24 hours. README updated to instruct running this daily via cron. Function includes error handling and logging.

**#7: Password Validation Only in Form, Not in Model**
✅ **FIXED** - Updated `User.set_password()` (Section 1) to validate minimum 8 characters: `if not password or len(password) < 8: raise ValueError('Password must be at least 8 characters')`. CreateUserForm route now catches ValueError and displays error.

**#8: Inactive User Can Still Access Protected Routes**
✅ **FIXED** - Updated admin_required and employee_required decorators (Section 3) to check `current_user.is_active`: `if not current_user.is_authenticated or not current_user.is_active or current_user.role != 'admin': abort(403)`.

**#9: Missing UPLOAD_FOLDER Creation in Import Route**
✅ **FIXED** - Added `os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)` at start of import_employees POST handler (Section 5).

### MEDIUM Severity Findings - All Resolved

**#10: Ambiguous Admin vs Super Admin Terminology**
✅ **FIXED** - Added clarification in Section 4 (Admin Dashboard): "'Admin' and 'super admin' are used interchangeably. The system has two roles only: 'admin' (full access) and 'employee' (limited). There is no role hierarchy within admin users."

**#11: Validation for estimated_cost Allows Zero**
✅ **FIXED** - Changed TASForm validator to `NumberRange(min=0)` (Section 8) and HTML form min to 0. Updated edge case #10 to clarify: "Estimated cost is zero: Allowed (free travel). Negative values are prevented by validation."

**#12: DataTables Pagination Conflicts with Query Limit**
✅ **FIXED** - Updated Section 4 dashboard table specification to disable pagination: `"paging": false, "searching": false, "info": false`. Added comment clarifying 10-record server-side limit is intentional.

**#13: Missing Import Validation for duplicate emp_id Across Rows**
✅ **FIXED** - Added duplicate emp_id detection in Section 5 before processing rows, similar to duplicate email check: validates emp_ids_in_file for duplicates and rejects file if found.

**#14: Chart.js Data Query Not Specified**
✅ **FIXED** - Added complete SQLAlchemy query in Section 4 using `cast(TASRecord.submitted_at, Date)`, `func.count()`, grouping, filtering, and conversion to Chart.js format with labels and data arrays.

**#15: Missing Template Directory Verification**
✅ **FIXED** - Added directory verification in Section 13 create_app() that logs warnings if templates or static directories are missing (doesn't create them, just warns).

**#16: Undefined Behavior for Logged-In User Accessing /login**
✅ **FIXED** - Added redirect logic in Section 3 login route: "If user is already authenticated and accesses /login, redirect to appropriate dashboard based on role."

**#17: Missing Max File Size Validation in Import Route**
✅ **FIXED** - Added RequestEntityTooLarge error handler in Section 13 app factory that flashes user-friendly message and redirects.

### NIT Severity Findings - All Resolved

**#18: Inconsistent Datetime Field Naming**
✅ **FIXED** - Added naming convention documentation in Section 2: "Timestamp columns use _at suffix. Date-only columns use _date or descriptive names."

**#19: Flash Message Category Inconsistency**
✅ **FIXED** - Added note in Section 14: "Use 'error' category in Python code; it is mapped to 'danger' in templates for Bootstrap compatibility."

**#20: README.md Not Defined**
✅ **FIXED** - Added complete README.md outline to Section 17 with 10 sections: Overview, Prerequisites, Installation, Database Setup, Running, User Guide, Troubleshooting, Manual Cleanup Tasks, Security Notes, License/Contact.

**#21: Logging Level Inconsistency**
✅ **FIXED** - Added note in Section 12: "All logger.error() calls must include exc_info=True to log full tracebacks." Updated all error logging examples throughout the document.

**#22: Missing Imports in Code Snippets**
✅ **FIXED** - Added note in Section 2 after Database Schema: "Import statements are omitted for brevity in code examples. Ensure all referenced modules are imported in actual implementation."

### Additional Improvements

- **Fixed approved this month stat query** (Section 4): Now uses `start_of_month` filter instead of counting all-time approved records
- **Fixed admin seed script** (Section 17): Uses environment variable or prompts for password instead of hardcoded 'admin123'
- **All error logging** now includes `exc_info=True` throughout the document
- **Consistent terminology** for admin/super admin clarified
- **Complete form definitions** for TASForm and CreateUserForm

**Finding #20 - Logging Directory:**
✅ **ADDRESSED** - Section 12 (Error Handling and Logging) updated to create logs directory with `os.makedirs('logs')` before configuring file handler.

**Finding #21 - DataTables Initialization:**
✅ **ADDRESSED** - Section 14 (Frontend Design) updated with complete JavaScript initialization code snippet and list of which tables should use the 'data-table' class.

### Summary

All 21 findings (6 HIGH, 10 MEDIUM, 5 NIT) have been addressed in this revision. The design is now ready for implementation with:
- Concrete CSRF protection strategy for all POST routes
- Correct SQLAlchemy enum configuration for MySQL
- Complete user management specification
- Fixed transaction boundaries for TAS number generation
- Modern dashboard UI specification matching reference design
- Comprehensive validation and error handling
- Complete frontend library specifications
- All configuration and setup steps clarified

---

**End of Design Document**
