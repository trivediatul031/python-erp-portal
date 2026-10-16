# Implementation Plan: Travel Approval System (TAS) ERP Portal

This plan implements a complete Python Flask + MySQL Travel Approval System ERP portal with super admin dashboard, employee portal, TAS number generation (TAS-{EMPID}-{SEQ}), import/export capabilities, and modern UI matching the reference screenshots.

**Design Authority:** This plan implements `design.md` with ALL findings from `design-review.md` resolved (10 findings: 6 HIGH, 4 MEDIUM).

**Project Structure:** c:\Users\AtulTrivedi\erpportalflask (greenfield - only .git and .agents exist)

---

## Phase 1: Foundation & Configuration

### 1. Create Project Structure and Configuration Files

- [ ] Create the complete directory tree: app/ with __init__.py, models.py, forms.py, utils.py, auth.py; app/routes/ with __init__.py, auth.py, admin.py, employee.py; app/templates/ with base.html, login.html, admin/, employee/ subdirs; app/static/ with css/, js/, uploads/ subdirs
- [ ] Create config.py with Config, DevelopmentConfig, ProductionConfig classes; include SECRET_KEY (from env), SQLALCHEMY_DATABASE_URI (mysql+pymysql://root:password@localhost/tas_erp), SQLALCHEMY_ENGINE_OPTIONS with isolation_level='READ COMMITTED', pool_pre_ping=True, pool_size=10, max_overflow=20 (FINDING #6); UPLOAD_FOLDER, MAX_CONTENT_LENGTH=10MB, WTF_CSRF_ENABLED=True, session security settings
- [ ] Create requirements.txt with exact versions: Flask==2.3.3, SQLAlchemy==2.0.20, Flask-Login==0.6.2, Flask-WTF==1.1.1, Flask-Bcrypt==1.0.1, PyMySQL==1.1.0, pandas==2.1.0, openpyxl==3.1.2, Werkzeug==2.3.7, python-dotenv==1.0.0
- [ ] Create .env.example with FLASK_APP, FLASK_ENV, SECRET_KEY, DATABASE_URL placeholders
- [ ] Create run.py application entry point that calls create_app()
- [ ] Create README.md with setup instructions, database initialization steps, verification procedure, and cleanup_old_exports() cron/scheduler note

**Files:** config.py, requirements.txt, run.py, .env.example, README.md, app/__init__.py, app/models.py, app/forms.py, app/utils.py, app/auth.py, app/routes/__init__.py, app/routes/auth.py, app/routes/admin.py, app/routes/employee.py, app/templates/base.html, app/templates/login.html, app/templates/admin/.gitkeep, app/templates/employee/.gitkeep, app/static/css/style.css, app/static/js/main.js, app/static/uploads/.gitkeep

**Verify:** Run `python --version` (ensure 3.9+), create virtual environment `python -m venv venv`, activate `venv\Scripts\activate`, install dependencies `pip install -r requirements.txt` — all packages install without errors.

---

### 2. Create Database Schema with Design Review Fixes

- [ ] Create schema.sql with MySQL database and table definitions
- [ ] Add `SET time_zone = '+00:00';` at the top of schema.sql (FINDING #5 - ensure MySQL uses UTC)
- [ ] Define tables: employees (emp_id VARCHAR(20) PK, name, email UNIQUE, department, designation, manager_id FK self-reference, is_active BOOLEAN DEFAULT TRUE, created_at, updated_at with CURRENT_TIMESTAMP), users (user_id INT AUTO_INCREMENT PK, username VARCHAR(50) UNIQUE, password_hash, role ENUM('admin','employee') native, emp_id FK, is_active, created_at, updated_at), tas_records (tas_id INT AUTO_INCREMENT PK, tas_number VARCHAR(30) UNIQUE, emp_id FK, travel_from, travel_to, travel_date_start DATE, travel_date_end DATE, purpose TEXT, estimated_cost DECIMAL(10,2), status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending', submitted_at, reviewed_at, reviewed_by FK users.user_id, rejection_reason TEXT, created_at, updated_at), tas_sequence (emp_id VARCHAR(20) PK FK, last_sequence INT DEFAULT 0)
- [ ] Add all indexes: idx_department, idx_manager, idx_email on employees; idx_username, idx_emp_id on users; idx_tas_number, idx_emp_id, idx_status, idx_submitted_at on tas_records
- [ ] All timestamp columns use MySQL server-side `DEFAULT CURRENT_TIMESTAMP` and `ON UPDATE CURRENT_TIMESTAMP` (no Python defaults)
- [ ] Include seed data: one admin user (username: admin, password: admin123, role: admin, emp_id: NULL, is_active: TRUE) with bcrypt hash

**Files:** schema.sql

**Verify:** Install MySQL 8.0+, run `mysql -u root -p < schema.sql`, verify tables created with `SHOW TABLES;`, verify admin user with `SELECT * FROM users;`, verify timezone with `SELECT @@session.time_zone;` (should return '+00:00').

---

### 3. Implement SQLAlchemy Models with Schema-First Strategy

- [ ] In app/__init__.py, create Flask app factory `create_app(config_name='default')` that loads config, ensures UPLOAD_FOLDER exists, warns if templates/ or static/ missing (don't create), initializes db, login_manager, csrf, bcrypt, registers error handler for RequestEntityTooLarge (10MB limit)
- [ ] Define SQLAlchemy instances: db = SQLAlchemy(), login_manager = LoginManager(), csrf = CSRFProtect(), bcrypt = Bcrypt()
- [ ] Implement Employee model with emp_id PK, name, email UNIQUE, department, designation, manager_id self-FK, is_active, created_at, updated_at (NO defaults/onupdate in Python - schema.sql handles it, FINDING #1); relationships: tas_records, user
- [ ] Implement User model with UserMixin, user_id PK, username UNIQUE, password_hash, role SQLAEnum('admin','employee', native_enum=True to match schema), emp_id FK, is_active, created_at, updated_at (NO defaults/onupdate); methods: set_password(password) with min 8 char validation raising ValueError, check_password(password), get_id() that validates self.user_id is not None before returning str(self.user_id) (FINDING #3)
- [ ] Implement TASRecord model with tas_id PK, tas_number UNIQUE, emp_id FK, travel_from, travel_to, travel_date_start, travel_date_end, purpose, estimated_cost Numeric(10,2), status SQLAEnum('Pending','Approved','Rejected', native_enum=True), submitted_at, reviewed_at, reviewed_by FK, rejection_reason (NO defaults)
- [ ] Implement TASSequence model with emp_id PK FK, last_sequence Integer (NO default)
- [ ] Configure Flask-Login: login_manager.login_view = 'auth.login', user_loader that converts user_id string to int with try/except (ValueError, TypeError) returning None on error (FINDING #3), login_message settings

**Files:** app/__init__.py, app/models.py

**Verify:** Run `python -c "from app import create_app; app = create_app(); print('App created')"` — no import errors. Run `python -c "from app import create_app, db; from app.models import User, Employee, TASRecord, TASSequence; app = create_app(); with app.app_context(): print(User.__tablename__, Employee.__tablename__)"` — prints table names.

---

## Phase 2: Authentication & Access Control

### 4. Implement Authentication Routes and Decorators

- [ ] In app/auth.py, implement decorators: @admin_required checks current_user.is_authenticated AND current_user.is_active AND current_user.role == 'admin' else abort(403); @employee_required same pattern for role == 'employee'
- [ ] In app/routes/auth.py, create auth_bp blueprint
- [ ] Implement GET /login: if current_user.is_authenticated redirect to role-based dashboard (admin → /admin/dashboard, employee → /employee/dashboard); else render login.html
- [ ] Implement POST /login: validate username/password, check is_active (if False: flash "Account is inactive. Contact administrator." and do NOT call login_user), if valid call login_user() and redirect to role-based dashboard; if invalid flash "Invalid username or password"
- [ ] Implement /logout: call logout_user() and redirect to /login
- [ ] Create LoginForm in app/forms.py with username (DataRequired), password (DataRequired), submit fields; CSRF auto-protected by FlaskForm

**Files:** app/auth.py, app/routes/auth.py, app/forms.py, app/templates/login.html

**Verify:** Start dev server `flask run`, navigate to http://localhost:5000/login, verify redirect loop doesn't occur if already logged in, attempt login with seeded admin user (admin/admin123), verify redirect to /admin/dashboard (will 404 for now, that's expected), verify logout redirects to /login, verify inactive user cannot login.

---

## Phase 3: Admin Dashboard & Statistics

### 5. Implement Admin Dashboard with Modern UI

- [ ] In app/templates/base.html, create base template with Bootstrap 5.3 CDN links, jQuery 3.7, DataTables 1.13, Chart.js 4.x CDN; include nav structure (top blue bar #4F46E5 with logo, search, user profile dropdown), left sidebar (240px, links to dashboard, tas_records, import_employees, export_tas, user_management with active state blue left border), main content area with {% block content %}, flash message handling (error → alert-danger, success/warning/info map directly); load app/static/css/style.css and app/static/js/main.js
- [ ] In app/static/css/style.css, define CSS variables for color palette (--primary-blue: #4F46E5, --success-green: #10B981, --warning-orange: #F59E0B, --info-purple: #A855F7, --danger-red: #EF4444, --bg-light: #F9FAFB, card colors: --card-purple: #E9D5FF, --card-green: #D1FAE5, --card-blue: #DBEAFE, --card-peach: #FED7AA); style sidebar, stat cards (rounded corners, subtle shadow), responsive grid (4 cards → 2x2 tablet → 1x4 mobile), sidebar collapse to hamburger on mobile
- [ ] In app/routes/admin.py, create admin_bp blueprint, implement GET /admin/dashboard with @admin_required: query total TAS submissions count, pending count, approved this month count (filter submitted_at >= start_of_month with month calculated as first day of current month), rejected count with rejection rate %; query TAS submissions by date for last 7 days using func.count + cast(submitted_at, Date) group by date; query status breakdown counts for Pending/Approved/Rejected; query 10 most recent TAS with employee join ordered by submitted_at desc; pass all data to template
- [ ] Create app/templates/admin/dashboard.html extending base.html: 4 stat cards (TOTAL TAS purple card-purple, PENDING APPROVALS green card-green, APPROVED blue card-blue, REJECTED orange card-peach with rejection rate); charts section with left 8/12 line chart "TAS Submissions Over Time" (Chart.js with data from backend, primary-blue line), right 4/12 status breakdown with colored progress bars; recent submissions table (10 rows, TAS Number, Employee Name, Destination, Travel Date, Status, each row links to /admin/tas/<tas_id>) with DataTables but paging/searching false (see design Section 4); "View All TAS Records" link button to /admin/tas_list
- [ ] In app/static/js/main.js, initialize Chart.js for dashboard (line chart with labels and data passed from template via JSON), initialize DataTables on dashboard-recent-table with paging false, searching false, info false, order [[0, "desc"]]

**Files:** app/templates/base.html, app/static/css/style.css, app/routes/admin.py, app/templates/admin/dashboard.html, app/static/js/main.js

**Verify:** Login as admin, navigate to /admin/dashboard, verify 4 stat cards display (counts will be zero initially), verify line chart renders empty (no data yet), verify recent table is empty with headers, verify sidebar navigation links, verify responsive layout by resizing browser (cards reflow, sidebar hamburger appears on mobile width).

---

## Phase 4: Employee Management & Import

### 6. Implement Employee Import with HR Excel/CSV Upload

- [ ] In app/forms.py, create ImportEmployeeForm with file field (FileRequired, FileAllowed(['xlsx', 'csv'])), submit
- [ ] In app/routes/admin.py, implement GET /admin/import_employees with @admin_required: render form
- [ ] Implement POST /admin/import_employees: validate file presence and extension (.xlsx/.csv), save to UPLOAD_FOLDER with secure_filename(), read with pandas (read_excel or read_csv), validate required columns [emp_id, name, email] present, validate row limit ≤ 1000, validate no duplicate emp_id within file (use duplicated()), validate no duplicate email within file; iterate rows with per-row validation: emp_id non-empty max 20 chars, name non-empty max 255 chars, email valid regex and max 255 chars, manager_id parsing with pd.isna() check then str().strip() then check for ['', 'none', 'null', 'n/a', 'na'] (FINDING #9), validate manager_id != emp_id, detect simple two-way circular reference (A→B, B→A within file); create or update Employee record per row with individual try/except and db.session.commit() per row (partial success by design, FINDING #7), collect errors; display flash with success_count and up to 10 errors; cleanup temp file in finally block with try/except on os.remove()
- [ ] Create app/templates/admin/import_employees.html extending base.html: form with file input (accept .xlsx,.csv), validation info (required columns, row limit, format rules), submit button
- [ ] Create sample_employees.csv in project root with columns: emp_id, name, email, department, designation, manager_id; include 5 sample rows (e.g., 1987, John Doe, john@example.com, IT, Manager, NULL)

**Files:** app/forms.py, app/routes/admin.py, app/templates/admin/import_employees.html, sample_employees.csv

**Verify:** Navigate to /admin/import_employees, upload sample_employees.csv, verify flash "Successfully imported 5 employees", check database `SELECT * FROM employees;` shows 5 rows, re-upload same file and verify updates (not duplicates), upload file with errors (invalid email, missing column) and verify error messages, upload file > 10MB and verify "File too large" error.

---

### 7. Implement User Management and User Creation

- [ ] In app/forms.py, create CreateUserForm with username (DataRequired, Length(3,50), Regexp(r'^[a-zA-Z0-9_]+$')), password (DataRequired, Length(min=8)), role SelectField choices=[('admin','Admin'),('employee','Employee')], emp_id SelectField (Optional, coerce=lambda x: x or None), is_active BooleanField default True, submit; add validate_emp_id method: if role=='employee' and not emp_id raise ValidationError 'Employee ID required for employee role'
- [ ] In app/routes/admin.py, implement GET /admin/user_management with @admin_required: query all users with employee join, render list table (Username, Role, Linked Employee name+emp_id, Status, Actions), "Create New User" button links to /admin/create_user
- [ ] Implement GET /admin/create_user: populate emp_id choices with employees not linked to any user (LEFT JOIN users WHERE user_id IS NULL), add ('', 'None (for admin users)') option; render form
- [ ] Implement POST /admin/create_user: validate form, check role=='employee' requires emp_id, check emp_id not already linked (double-check), create User with set_password (catches ValueError for min 8 chars), db.session.add and commit with try/except (ValueError for password, IntegrityError for duplicate username/emp_id), flash success or error, redirect to user_management
- [ ] Create app/templates/admin/user_management.html extending base.html: table with users list, create button
- [ ] Create app/templates/admin/create_user.html extending base.html: form with fields (username, password, role dropdown, emp_id dropdown populated from backend, is_active checkbox), validation errors display, submit button

**Files:** app/forms.py, app/routes/admin.py, app/templates/admin/user_management.html, app/templates/admin/create_user.html

**Verify:** Navigate to /admin/user_management, verify admin user listed, click "Create New User", create employee user linked to imported employee (e.g., username: john_doe, password: password123, role: employee, emp_id: 1987), verify success flash, check database `SELECT * FROM users;` shows new user, attempt duplicate username and verify error, create admin user without emp_id and verify success.

---

## Phase 5: TAS Submission & Number Generation

### 8. Implement TAS Number Generation with Race Condition Handling

- [ ] In app/utils.py, implement generate_tas_number(emp_id) function: query TASSequence with with_for_update() lock, wrap in try/except IntegrityError with max_retries=3 loop (FINDING #4); if seq_record None create TASSequence(emp_id, last_sequence=1) and db.session.flush() to detect conflict immediately, else increment last_sequence; format tas_number as f"TAS-{emp_id}-{seq_record.last_sequence:04d}"; on IntegrityError rollback and retry (another transaction inserted first), after 3 retries raise RuntimeError; return tas_number WITHOUT committing (caller commits both sequence and TAS record together)
- [ ] Add error handling note in utils.py docstring: "Must be called within active transaction. Caller responsible for commit. IntegrityError during first insert is retried up to 3 times. After 3 failures raises RuntimeError."

**Files:** app/utils.py

**Verify:** Write test script that imports create_app, db, models, generate_tas_number; in app context, create test employee if not exists, call generate_tas_number('1987') multiple times in separate transactions and verify sequential numbers TAS-1987-0001, TAS-1987-0002, TAS-1987-0003; verify db.session.commit() in caller finalizes both tas_sequence and tas_records together.

---

### 9. Implement Employee TAS Submission Form

- [ ] In app/forms.py, create TASForm with travel_from (DataRequired, Length(max=255)), travel_to (DataRequired, Length(max=255)), travel_date_start DateField (DataRequired), travel_date_end DateField (DataRequired), purpose TextAreaField (DataRequired, Length(max=1000)), estimated_cost DecimalField (DataRequired, NumberRange(min=0)), submit; add validate_travel_date_start method: if field.data < date.today() raise ValidationError 'Travel start date cannot be in the past'; add validate_travel_date_end method: if hasattr(self.travel_date_start, 'data') and field.data < self.travel_date_start.data raise ValidationError 'Travel end date must be after start date'
- [ ] In app/routes/employee.py, create employee_bp blueprint, implement GET /employee/submit_tas with @employee_required: render form
- [ ] Implement POST /employee/submit_tas: validate form, check current_user.emp_id not None (if None flash error "Your account is not linked to an employee record. Contact admin." and redirect to dashboard), call generate_tas_number(emp_id) within transaction, create TASRecord with form data and tas_number and status='Pending', db.session.add, db.session.commit() to commit both sequence update and TAS record together, flash success with tas_number, redirect to /employee/tas_history; wrap in try/except Exception for database errors: db.session.rollback(), log error with exc_info=True, flash "Failed to submit TAS. Please try again."
- [ ] Create app/templates/employee/submit_tas.html extending base.html: form with fields (travel_from text, travel_to text, travel_date_start date picker, travel_date_end date picker, purpose textarea, estimated_cost number input min=0 step=0.01), Bootstrap styling, validation error display, submit button

**Files:** app/forms.py, app/routes/employee.py, app/templates/employee/submit_tas.html

**Verify:** Create employee user if not exists, login as employee, navigate to /employee/submit_tas, fill form (From: New York, To: San Francisco, Start: tomorrow, End: day after, Purpose: Client meeting, Cost: 1500.00), submit, verify flash "TAS submitted successfully. Your TAS number is TAS-1987-0001", check database `SELECT * FROM tas_records;` and `SELECT * FROM tas_sequence;` verify tas_number and last_sequence incremented, submit again and verify TAS-1987-0002.

---

### 10. Implement Employee Dashboard and TAS History

- [ ] In app/routes/employee.py, implement GET /employee/dashboard with @employee_required: query employee's recent TAS records (limit 5), calculate summary stats (total submissions, pending count), render dashboard with welcome message, quick links (Submit New TAS, View History), recent submissions summary table
- [ ] Implement GET /employee/tas_history with @employee_required: check current_user.emp_id not None, query TASRecord.filter_by(emp_id=emp_id).order_by(submitted_at desc), render table with TAS Number, Destination (travel_to), Travel Dates (start to end), Status, Submitted Date, each row links to /employee/tas/<tas_id>
- [ ] Implement GET /employee/tas/<int:tas_id> with @employee_required: query TAS by tas_id, validate TAS.emp_id == current_user.emp_id else abort(403), render detailed view with all TAS fields, employee info, approval info if approved/rejected
- [ ] Create app/templates/employee/dashboard.html extending base.html: welcome card with user's name, quick action buttons, summary stats cards (smaller versions), recent submissions table
- [ ] Create app/templates/employee/tas_history.html extending base.html: table with all employee's TAS records, DataTables with paging/searching enabled (class="data-table"), Bootstrap styling, status badges (Pending: yellow, Approved: green, Rejected: red)
- [ ] Create app/templates/employee/tas_detail.html extending base.html: detailed TAS info card, employee info, travel details, status badge, approval/rejection info if processed
- [ ] In app/static/js/main.js, add DataTables initialization for .data-table class with pageLength 20, order [[0, "desc"]], search/pagination enabled

**Files:** app/routes/employee.py, app/templates/employee/dashboard.html, app/templates/employee/tas_history.html, app/templates/employee/tas_detail.html, app/static/js/main.js

**Verify:** Login as employee, navigate to /employee/dashboard, verify welcome message and summary stats, click "Submit New TAS" links to submit form, click "View History" navigates to /employee/tas_history, verify table shows submitted TAS records with TAS-1987-0001 and TAS-1987-0002, click TAS number to view detail, verify all information displayed correctly, verify DataTables search/sort/pagination work.

---

## Phase 6: TAS Approval Workflow

### 11. Implement Admin TAS List and Detail Views

- [ ] In app/routes/admin.py, implement GET /admin/tas_list with @admin_required: query all TASRecord with employee join, support query params for filters (status, date_from, date_to, department), apply filters to query, render table with TAS Number, Employee Name, Department, Destination (travel_to), Travel Start Date, Status, Submitted At, Actions (View, Approve if Pending, Reject if Pending); DataTables enabled (class="data-table")
- [ ] Implement GET /admin/tas/<int:tas_id> with @admin_required: query TAS by ID with employee join, if not found abort(404), render detailed view with all TAS info, employee details, approve/reject forms if status=='Pending'
- [ ] Create app/templates/admin/tas_list.html extending base.html: filter form (status dropdown, date_from/date_to date inputs, department text input, submit button), table with TAS records, DataTables class="data-table", action buttons per row (View, Approve/Reject if Pending)
- [ ] Create app/templates/admin/tas_detail.html extending base.html: TAS info card, employee info card, if status=='Pending' show two forms: Approve form (POST to /admin/tas/<tas_id>/approve with hidden CSRF token and submit button) and Reject form (POST to /admin/tas/<tas_id>/reject with hidden CSRF token, rejection_reason textarea max 500 chars, submit button); if already processed show approval/rejection info with reviewer name and timestamp

**Files:** app/routes/admin.py, app/templates/admin/tas_list.html, app/templates/admin/tas_detail.html

**Verify:** Login as admin, navigate to /admin/tas_list, verify TAS records display with employee info, verify filters work (status=Pending shows only pending, date range filters), click TAS number to view detail, verify detail page shows all info, verify Approve and Reject forms display for Pending TAS with CSRF tokens (inspect HTML source to confirm csrf_token hidden field).

---

### 12. Implement TAS Approve and Reject Actions with Manual CSRF Validation

- [ ] In app/routes/admin.py, implement POST /admin/tas/<int:tas_id>/approve with @admin_required: manually validate CSRF token with try/except around validate_csrf(request.form.get('csrf_token')), on ValidationError abort(403) (FINDING #2); query TAS by ID, if not found abort(404), if status != 'Pending' flash "TAS has already been processed" and redirect to detail, update status='Approved', reviewed_at=datetime.utcnow(), reviewed_by=current_user.user_id, db.session.commit() with try/except (log error, flash "Error updating TAS status"), flash success "TAS approved successfully", redirect to /admin/tas/<tas_id>
- [ ] Implement POST /admin/tas/<int:tas_id>/reject with @admin_required: same CSRF validation pattern; query TAS, validate Pending status, get rejection_reason from request.form (max 500 chars), update status='Rejected', reviewed_at=datetime.utcnow(), reviewed_by=current_user.user_id, rejection_reason=rejection_reason[:500], db.session.commit() with error handling, flash success "TAS rejected", redirect to detail
- [ ] Import validate_csrf from flask_wtf.csrf and ValidationError from wtforms at top of admin.py

**Files:** app/routes/admin.py

**Verify:** Login as admin, navigate to pending TAS detail, click "Approve" button, verify redirect to detail with success flash, verify status changed to "Approved" in database and UI, verify reviewed_at and reviewed_by set correctly; create another TAS as employee, login as admin, navigate to that TAS detail, click "Reject" with reason "Budget exceeded", verify status="Rejected" and rejection_reason saved; attempt to approve already-processed TAS and verify error flash "TAS has already been processed".

---

## Phase 7: Data Export & Reporting

### 13. Implement TAS Records Export with Filter Support

- [ ] In app/routes/admin.py, implement GET /admin/export_tas with @admin_required: parse query params (format=[xlsx|csv] default xlsx, status=[All|Pending|Approved|Rejected] default All, date_from YYYY-MM-DD optional, date_to YYYY-MM-DD optional, department optional); validate date format with try/except ValueError, if date_from > date_to return 400 error "date_from must be before date_to"; build query with TASRecord join Employee, apply status filter if not 'All', apply date_from filter (submitted_at >= date_from_obj), apply date_to filter with +1 day trick (submitted_at < date_to_obj + timedelta(days=1)) to include full date_to (FINDING #10), apply department filter if provided; execute query.all() with results; handle empty results: if not results create empty DataFrame with explicit columns (FINDING #8) else create DataFrame from results; generate timestamp filename tas_records_{timestamp}.{xlsx|csv}, save to UPLOAD_FOLDER with to_csv or to_excel; send_file with as_attachment, setup cleanup callback with response.call_on_close(cleanup_file) that tries os.remove with except logging warning
- [ ] In app/utils.py, add cleanup_old_exports(hours=24) function: iterate UPLOAD_FOLDER for files starting with 'tas_records_', check mtime < cutoff, os.remove with try/except, log info on success and error on failure
- [ ] Update README.md to note "Run cleanup_old_exports() daily via cron (Linux/Mac) or Task Scheduler (Windows) to remove export files older than 24 hours"

**Files:** app/routes/admin.py, app/utils.py, README.md

**Verify:** Login as admin, navigate to /admin/export_tas (or use query params in URL), test export with format=xlsx and status=Pending, verify file downloads as tas_records_YYYYMMDD_HHMMSS.xlsx, open in Excel and verify columns and data correct, test export with empty results (status=Rejected if no rejected TAS yet) and verify file has headers only, test export with date range filters and verify only records in range exported, test format=csv and verify CSV file downloads, check UPLOAD_FOLDER after download and verify cleanup callback removed file (may need to test with curl or programmatic request).

---

## Phase 8: Error Handling & Polish

### 14. Implement Error Pages and Logging Configuration

- [ ] In app/__init__.py, register error handlers for 403, 404, 500: create custom templates (app/templates/errors/403.html, 404.html, 500.html) with Bootstrap styling, friendly messages, links back to dashboard
- [ ] Configure logging in create_app: if not app.debug, create logs/ directory, setup RotatingFileHandler('logs/erpportal.log', maxBytes=10MB, backupCount=10), set formatter with timestamp/level/message/location, setLevel INFO, add to app.logger, log "ERP Portal startup"
- [ ] Review all routes and ensure every exception is caught with db.session.rollback() where applicable, app.logger.error() with exc_info=True, and user-friendly flash message
- [ ] Create app/templates/errors/403.html: "Access Denied. You do not have permission to view this page." with link to appropriate dashboard based on role
- [ ] Create app/templates/errors/404.html: "Page Not Found. The page you are looking for does not exist." with link to /admin/dashboard or /employee/dashboard
- [ ] Create app/templates/errors/500.html: "Internal Server Error. Something went wrong. Please try again later." with link to dashboard

**Files:** app/__init__.py, app/templates/errors/403.html, app/templates/errors/404.html, app/templates/errors/500.html

**Verify:** Login as employee, attempt to access /admin/dashboard, verify 403 error page displays with link to /employee/dashboard; navigate to non-existent URL /admin/nonexistent, verify 404 error page; simulate 500 error by temporarily breaking database connection (stop MySQL), attempt TAS submission, verify 500 error page or graceful error handling with flash message; restart MySQL, check logs/erpportal.log file exists with startup message and error entries with full tracebacks.

---

### 15. Final UI Polish and Responsive Testing

- [ ] Review app/static/css/style.css and ensure all components styled per color palette: stat cards with rounded corners and shadows, forms with Bootstrap classes, tables responsive with horizontal scroll on small screens, buttons with appropriate colors (success green, danger red, primary blue), sidebar with active state highlighting
- [ ] In app/templates/base.html, ensure flash messages styled correctly with alert-dismissible close button, ensure nav dropdown works for user profile, ensure sidebar hamburger toggle implemented for mobile (Bootstrap collapse or custom JS)
- [ ] In app/static/js/main.js, ensure Chart.js initialization handles empty data gracefully (no errors in console if chart data empty), ensure DataTables initialization applied to .data-table class with correct settings (dashboard-recent-table special case with paging/searching false), add form validation enhancement if needed (e.g., date range validation on client side)
- [ ] Test responsive layout: resize browser to mobile width (< 768px), verify sidebar collapses to hamburger, verify stat cards stack vertically, verify tables horizontally scrollable, verify forms adapt to narrow width, verify charts resize appropriately
- [ ] Test all navigation flows: login → dashboard → submit TAS → view history → logout; admin login → dashboard → view TAS list → approve TAS → import employees → create user → export data → logout
- [ ] Test edge cases: employee without emp_id attempts TAS submission, inactive user attempts login, duplicate TAS number generation (retry logic), concurrent TAS submissions for same employee (race condition), export with no results, import with errors, CSRF token validation on approve/reject

**Files:** app/static/css/style.css, app/templates/base.html, app/static/js/main.js

**Verify:** Complete manual testing checklist: (1) Admin can login and see dashboard with stats, (2) Admin can import employees from sample_employees.csv, (3) Admin can create employee user, (4) Employee can login and submit TAS receiving TAS-{EMPID}-0001, (5) Employee submits again and receives TAS-{EMPID}-0002, (6) Admin views TAS list and approves one TAS, (7) Admin rejects one TAS with reason, (8) Admin exports TAS records to Excel and CSV, (9) Employee views TAS history with approved/rejected status, (10) Logout works for both roles, (11) Responsive layout works on mobile width, (12) All forms have CSRF protection, (13) Error pages display correctly, (14) Logs capture errors with tracebacks.

---

## Verification Procedure

**Prerequisites:**
- Python 3.9+ installed
- MySQL 8.0+ installed and running
- Virtual environment activated

**Setup Steps:**
1. Install dependencies: `pip install -r requirements.txt`
2. Copy .env.example to .env and set SECRET_KEY, DATABASE_URL (mysql+pymysql://root:password@localhost/tas_erp)
3. Create database: `mysql -u root -p -e "CREATE DATABASE tas_erp;"`
4. Run schema: `mysql -u root -p tas_erp < schema.sql`
5. Verify timezone: `mysql -u root -p tas_erp -e "SELECT @@session.time_zone;"` (should be '+00:00')
6. Verify tables: `mysql -u root -p tas_erp -e "SHOW TABLES;"` (should show 4 tables)
7. Verify admin user: `mysql -u root -p tas_erp -e "SELECT username, role FROM users WHERE role='admin';"` (should show admin user)

**Functional Testing:**
1. Start server: `flask run` (or `python run.py`)
2. Navigate to http://localhost:5000/login
3. Login as admin (username: admin, password: admin123)
4. Verify dashboard displays with 4 stat cards (all zero initially)
5. Import employees: navigate to /admin/import_employees, upload sample_employees.csv, verify success message
6. Verify employees in database: `mysql -u root -p tas_erp -e "SELECT emp_id, name, email FROM employees;"`
7. Create employee user: navigate to /admin/create_user, create user (username: test_emp, password: password123, role: employee, link to imported employee), verify success
8. Logout, login as employee (test_emp/password123)
9. Submit TAS: navigate to /employee/submit_tas, fill form (From: NYC, To: SF, Start: tomorrow, End: day after tomorrow, Purpose: Meeting, Cost: 1500), submit
10. Verify TAS number displayed: "TAS submitted successfully. Your TAS number is TAS-{EMPID}-0001"
11. Verify TAS in database: `mysql -u root -p tas_erp -e "SELECT tas_number, emp_id, status FROM tas_records;"`
12. Submit second TAS and verify TAS-{EMPID}-0002 generated
13. Verify sequence: `mysql -u root -p tas_erp -e "SELECT emp_id, last_sequence FROM tas_sequence;"`
14. View TAS history: navigate to /employee/tas_history, verify both TAS records display
15. Logout, login as admin
16. Navigate to /admin/tas_list, verify TAS records display with employee info
17. Click first TAS, view detail, click "Approve", verify success message and status changed
18. Navigate to second TAS, click "Reject", enter reason "Budget exceeded", verify success
19. Navigate to dashboard, verify stats updated (Pending: 0, Approved: 1, Rejected: 1, Total: 2)
20. Export data: navigate to /admin/export_tas?format=xlsx&status=Approved, verify file downloads and contains approved TAS
21. Export with date range: test with date_from and date_to parameters, verify filtering works
22. Test responsive: resize browser to mobile width, verify sidebar collapses, cards reflow

**Security Testing:**
1. Verify CSRF on approve: inspect approve form HTML source, confirm csrf_token hidden field present
2. Verify CSRF on reject: same for reject form
3. Attempt to access /admin/dashboard as employee role: verify 403 Forbidden
4. Attempt to access /employee/dashboard as admin role: verify 403 Forbidden (or allowed if admin can view employee dashboard is acceptable)
5. Attempt to view another employee's TAS detail: login as employee, manually navigate to /employee/tas/<other_employee_tas_id>, verify 403
6. Verify inactive user cannot login: update user is_active=FALSE in database, attempt login, verify error message

**Concurrency Testing (Optional but Recommended):**
1. Write Python script to simulate concurrent TAS submissions for same employee (use threading or multiprocessing)
2. Submit 10 concurrent TAS requests for same emp_id
3. Verify all 10 TAS numbers generated with unique sequential numbers (no duplicates)
4. Verify tas_sequence.last_sequence = 10 for that employee
5. If any IntegrityError occurs during race condition, verify retry logic succeeded (check logs for retry messages)

**Log Verification:**
1. Check logs/erpportal.log exists
2. Verify startup message present
3. Simulate error (e.g., break database connection), attempt TAS submission, verify error logged with full traceback (exc_info=True includes stack trace)

**Cleanup:**
1. Test cleanup_old_exports() function: create old test file in UPLOAD_FOLDER with mtime > 24 hours ago, run function, verify file deleted

---

## Design Review Findings Resolution Summary

All 10 findings from design-review.md are resolved in this plan:

1. **HIGH #1 - Database Init Conflict:** Schema-first strategy adopted. SQLAlchemy models have NO defaults/onupdate for timestamp columns. schema.sql is single source of truth for defaults. Step 3 implements this.

2. **HIGH #2 - CSRF Validation Missing:** Manual CSRF validation added to approve_tas and reject_tas routes using validate_csrf(request.form.get('csrf_token')) with abort(403) on ValidationError. Step 12 implements this.

3. **HIGH #3 - User.get_id() Type Safety:** User.get_id() validates user_id is not None before returning str(user_id). user_loader wraps int(user_id) in try/except (ValueError, TypeError) returning None on error. Step 3 implements this.

4. **HIGH #4 - TAS Number Race Condition:** generate_tas_number() wraps TASSequence creation in try/except IntegrityError with max_retries=3, uses db.session.flush() to detect conflict immediately, retries on collision. Step 8 implements this.

5. **HIGH #5 - Timestamp UTC Assumption:** schema.sql has `SET time_zone = '+00:00';` at top. README documents MySQL timezone configuration. Models do NOT use datetime.utcnow defaults (schema-first). Step 2 implements this.

6. **HIGH #6 - Transaction Isolation Level:** Config.SQLALCHEMY_ENGINE_OPTIONS includes isolation_level='READ COMMITTED', pool_pre_ping=True, pool_size=10, max_overflow=20. Step 1 implements this.

7. **MEDIUM #7 - Import Partial Success:** Employee import commits per-row (partial success by design). README and code comments document this behavior. Alternative all-or-nothing approach noted in comments. Step 6 implements this.

8. **MEDIUM #8 - Export Zero Results:** Export route checks `if not results: df = pd.DataFrame(columns=[...])` to create empty DataFrame with headers explicitly. Step 13 implements this.

9. **MEDIUM #9 - Manager ID Null Handling:** Import employee parsing uses pd.isna() for NaN, then checks manager_id.lower() in ['', 'none', 'null', 'n/a', 'na'] to handle common null representations. Step 6 implements this.

10. **MEDIUM #10 - Date Filter Time Component:** Export route date_to filter uses `date_to_obj + timedelta(days=1)` with `<` operator to include entire date_to. Step 13 implements this.

---

## Notes

- **Build Order:** Dependencies dictate order: foundation → auth → models → UI → features. Each step leaves codebase buildable.
- **Verification Strategy:** Each step has concrete verify command using actual project tools (flask run, mysql CLI, browser testing, database queries).
- **Import Pattern:** All imports assumed in examples. Actual implementation must import: datetime, os, re, pandas, sqlalchemy.func, flask modules, werkzeug.security, flask_login, flask_wtf, etc.
- **Error Handling:** Every database operation wrapped in try/except with rollback, logging (exc_info=True), and user-friendly flash message.
- **Security:** CSRF on all forms, role-based access control, SQL injection prevention via ORM, input validation, secure session cookies.
- **Concurrency:** TAS number generation is concurrency-safe via SELECT FOR UPDATE and IntegrityError retry logic.
- **Timezone:** MySQL configured to UTC, all timestamps use server-side defaults for consistency.
- **File Cleanup:** Export files auto-cleanup via response callback; cleanup_old_exports() scheduled job handles stale files.

