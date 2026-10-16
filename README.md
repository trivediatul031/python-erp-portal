# TAS ERP - Travel Approval System

An Enterprise Resource Planning portal for managing employee travel approval requests.

## Overview

The TAS ERP system provides a web-based interface for employees to submit travel approval requests (TAS) and for administrators to review, approve, or reject them. The system automatically generates unique TAS numbers in the format `TAS-EMPID-SEQUENCE` (e.g., TAS-1987-0001).

## Features

- **Super Admin Dashboard**: View all TAS records, import employee data from HR, export TAS records
- **Employee Dashboard**: Submit travel approval requests, track submission status
- **User Management**: Create and manage user accounts with role-based access
- **Automatic TAS Number Generation**: Unique sequential numbering per employee
- **Import/Export**: Import employee data from CSV/Excel, export TAS records

## Prerequisites

- Python 3.9 or higher
- MySQL 8.0 or higher
- pip (Python package manager)
- virtualenv (recommended)

## Setup Instructions

### 1. Clone or Extract the Project

```bash
cd erpportalflask
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Database

Copy `.env.example` to `.env` and update the configuration:

```bash
copy .env.example .env
```

Edit `.env` file:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URL=mysql+pymysql://username:password@localhost/tas_erp
```

### 6. Create Database

```bash
mysql -u root -p -e "CREATE DATABASE tas_erp;"
```

### 7. Apply Database Schema

```bash
mysql -u root -p tas_erp < schema.sql
```

### 8. Verify Timezone Configuration

Ensure MySQL session timezone is set to UTC:

```bash
mysql -u root -p tas_erp -e "SELECT @@session.time_zone;"
```

Expected output: `+00:00`

### 9. Verify Tables Created

```bash
mysql -u root -p tas_erp -e "SHOW TABLES;"
```

Expected tables:
- employees
- users
- tas_records
- tas_sequence

## Running the Application

### Development Mode

```bash
flask run
```

Or:

```bash
python run.py
```

The application will be available at `http://localhost:5000`

### Default Admin Credentials

- **Username**: admin
- **Password**: admin123

**Important**: Change the admin password after first login in production environments.

## Verification Steps

1. Start the development server: `flask run`
2. Navigate to `http://localhost:5000/login`
3. Login with admin credentials (admin/admin123)
4. Verify redirect to admin dashboard
5. Test logout functionality

## Project Structure

```
erpportalflask/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # SQLAlchemy models
│   ├── forms.py             # WTForms forms
│   ├── auth.py              # Role-based access decorators
│   ├── utils.py             # Utility functions
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication routes
│   │   ├── admin.py         # Admin routes
│   │   └── employee.py      # Employee routes
│   ├── templates/
│   │   ├── base.html        # Base template
│   │   ├── login.html       # Login page
│   │   ├── admin/           # Admin templates
│   │   ├── employee/        # Employee templates
│   │   └── errors/          # Error templates
│   └── static/
│       ├── css/
│       │   └── style.css    # Custom styles
│       ├── js/
│       │   └── main.js      # Custom scripts
│       └── uploads/         # Temporary file storage
├── config.py                # Configuration classes
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
├── schema.sql               # Database schema
└── README.md                # This file
```

## Database Schema

### Employees Table
- Stores employee information from HR
- `emp_id` (VARCHAR 20): Primary key
- `manager_id`: Self-referencing foreign key for organizational hierarchy

### Users Table
- Authentication and authorization
- Links to employees via `emp_id`
- Roles: 'admin' or 'employee'

### TAS Records Table
- Travel approval submissions
- Status: 'Pending', 'Approved', 'Rejected'
- Links to employee and reviewer (admin user)

### TAS Sequence Table
- Tracks last sequence number per employee
- Used for generating unique TAS numbers

## Maintenance

### Cleanup Old Export Files

The system creates temporary export files in `app/static/uploads/`. These files should be cleaned up regularly to prevent disk space issues.

#### Scheduled Cleanup

Run `cleanup_old_exports()` daily via cron (Linux/Mac) or Task Scheduler (Windows) to remove export files older than 24 hours.

**Example cron job (Linux/Mac):**
```bash
0 2 * * * /path/to/venv/bin/python -c "from app.utils import cleanup_old_exports; from app import create_app; app = create_app(); with app.app_context(): cleanup_old_exports(app.config['UPLOAD_FOLDER'])"
```

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to Daily at 2:00 AM
4. Action: Start a program
5. Program: `C:\path\to\venv\Scripts\python.exe`
6. Arguments: `-c "from app.utils import cleanup_old_exports; from app import create_app; app = create_app(); with app.app_context(): cleanup_old_exports(app.config['UPLOAD_FOLDER'])"`

**Manual cleanup:**
```python
from app import create_app
from app.utils import cleanup_old_exports

app = create_app()
with app.app_context():
    cleanup_old_exports(app.config['UPLOAD_FOLDER'], hours=24)
```

## Technology Stack

- **Backend**: Flask 2.3.3, SQLAlchemy 2.0.20
- **Database**: MySQL 8.0+ with PyMySQL connector
- **Authentication**: Flask-Login, Flask-Bcrypt
- **Frontend**: Bootstrap 5.3, jQuery 3.7, DataTables 1.13, Chart.js 4.x
- **Forms**: Flask-WTF with CSRF protection
- **Data Processing**: Pandas, openpyxl

## Security Features

- CSRF protection on all forms
- Password hashing with bcrypt
- Role-based access control
- Session security (HttpOnly, SameSite cookies)
- File upload size limits (10MB)
- Database transaction isolation (READ COMMITTED)

## Production Deployment

### Prerequisites for Production

1. **Generate a Secure SECRET_KEY**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Update `.env` file with the generated key:
```
SECRET_KEY=your-generated-secret-key-here
```

2. **Update Flask Environment**

Set Flask to production mode in `.env`:
```
FLASK_ENV=production
FLASK_DEBUG=False
```

3. **Enable Secure Cookies**

For HTTPS deployments, ensure `SESSION_COOKIE_SECURE=True` in your configuration. This prevents session cookies from being transmitted over unencrypted connections.

Update `config.py`:
```python
class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
```

4. **Verify MySQL Timezone Configuration**

Ensure MySQL session timezone is set to UTC:
```bash
mysql -u root -p tas_erp -e "SELECT @@session.time_zone;"
```

Expected output: `+00:00`

If not set, add to `my.cnf` or `my.ini`:
```
[mysqld]
default-time-zone='+00:00'
```

5. **File Permissions**

Ensure the application can write to the logs directory:

**Windows:**
```powershell
New-Item -ItemType Directory -Force -Path logs
icacls logs /grant:r "Users:(OI)(CI)F"
```

**Linux/Mac:**
```bash
mkdir -p logs
chmod 755 logs
```

Ensure UPLOAD_FOLDER is writable:
```bash
mkdir -p app/static/uploads
chmod 755 app/static/uploads
```

6. **Scheduled Cleanup Task**

Configure scheduled task to clean up old export files daily.

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task: "TAS ERP File Cleanup"
3. Trigger: Daily at 2:00 AM
4. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `-c "from app.utils import cleanup_old_exports; from app import create_app; app = create_app('production'); with app.app_context(): cleanup_old_exports(app.config['UPLOAD_FOLDER'])"`
   - Start in: `C:\path\to\erpportalflask`

**Linux/Mac Cron Job:**
```bash
# Edit crontab
crontab -e

# Add entry (runs daily at 2:00 AM)
0 2 * * * cd /path/to/erpportalflask && /path/to/venv/bin/python -c "from app.utils import cleanup_old_exports; from app import create_app; app = create_app('production'); with app.app_context(): cleanup_old_exports(app.config['UPLOAD_FOLDER'])" >> /path/to/logs/cleanup.log 2>&1
```

7. **Production Server**

Use a production WSGI server like Gunicorn (Linux/Mac) or Waitress (Windows).

**Gunicorn (Linux/Mac):**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
```

**Waitress (Windows):**
```bash
pip install waitress
waitress-serve --port=5000 run:app
```

8. **Reverse Proxy with Nginx**

Configure Nginx to proxy requests to the WSGI server and handle HTTPS:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/erpportalflask/app/static;
        expires 30d;
    }
}
```

## Troubleshooting

### Common Issues

#### 1. MySQL Timezone Not UTC

**Symptom:** Timestamps are incorrect in the database.

**Solution:** 
```bash
# Check current timezone
mysql -u root -p tas_erp -e "SELECT @@session.time_zone, @@global.time_zone;"

# Set timezone to UTC in my.cnf or my.ini
[mysqld]
default-time-zone='+00:00'

# Restart MySQL service
# Windows: net stop mysql80 && net start mysql80
# Linux: sudo systemctl restart mysql
```

#### 2. Logs Directory Permission Denied

**Symptom:** Application fails to start with "Permission denied" error for logs/erpportal.log.

**Solution:**
```bash
# Windows
icacls logs /grant:r "Users:(OI)(CI)F"

# Linux/Mac
chmod 755 logs
chown appuser:appuser logs
```

#### 3. UPLOAD_FOLDER Not Writable

**Symptom:** Import/export operations fail with "Permission denied" or "Cannot write to file".

**Solution:**
```bash
# Windows
icacls app\static\uploads /grant:r "Users:(OI)(CI)F"

# Linux/Mac
chmod 755 app/static/uploads
chown appuser:appuser app/static/uploads
```

#### 4. SECRET_KEY Not Set

**Symptom:** Application fails with "RuntimeError: The session is unavailable because no secret key was set."

**Solution:**
```bash
# Generate a secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Add to .env file
SECRET_KEY=your-generated-key-here
```

#### 5. CSRF Token Missing

**Symptom:** Forms fail with "400 Bad Request: The CSRF token is missing."

**Solution:** Ensure all forms include `{{ form.hidden_tag() }}` or manual CSRF token:
```html
<form method="POST">
    {{ form.hidden_tag() }}
    <!-- form fields -->
</form>
```

For manual forms without WTForms:
```html
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <!-- form fields -->
</form>
```

#### 6. Database Connection Failed

**Symptom:** "Can't connect to MySQL server" or "Access denied for user".

**Solution:**
- Verify MySQL is running: `mysql -u root -p`
- Check DATABASE_URL in `.env` file
- Verify database credentials
- Ensure database exists: `mysql -u root -p -e "SHOW DATABASES;"`

#### 7. Import Fails with "Missing required columns"

**Symptom:** Employee import shows error about missing columns.

**Solution:** Ensure CSV/Excel file has required columns: `emp_id`, `name`, `email`. Optional columns: `department`, `designation`, `manager_id`.

Example CSV format:
```csv
emp_id,name,email,department,designation,manager_id
1987,John Doe,john@example.com,IT,Developer,2001
```

#### 8. Export File Not Cleaned Up

**Symptom:** Export files accumulate in `app/static/uploads/`.

**Solution:**
- Verify `call_on_close()` is working (files should auto-delete after download)
- Run manual cleanup:
```python
from app import create_app
from app.utils import cleanup_old_exports

app = create_app()
with app.app_context():
    cleanup_old_exports(app.config['UPLOAD_FOLDER'], hours=24)
```
- Set up scheduled cleanup task (see Production Deployment section)

#### 9. Chart Not Displaying on Dashboard

**Symptom:** Dashboard chart area is blank.

**Solution:**
- Check browser console for JavaScript errors
- Verify Chart.js library is loaded
- Ensure `chartData` variable is properly passed from template
- Check that TAS records exist in database

#### 10. Responsive Layout Issues on Mobile

**Symptom:** Sidebar doesn't collapse or elements overflow on mobile.

**Solution:**
- Clear browser cache
- Test with browser DevTools mobile emulation
- Verify viewport meta tag in base.html:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

### Logging and Debugging

**View Application Logs:**
```bash
# View recent logs
tail -f logs/erpportal.log

# Windows PowerShell
Get-Content logs/erpportal.log -Tail 50 -Wait
```

**Enable Debug Mode (Development Only):**
```
FLASK_ENV=development
FLASK_DEBUG=True
```

**Database Query Logging:**
Add to config.py for development:
```python
SQLALCHEMY_ECHO = True  # Log all SQL queries
```

## Support

For issues or questions, contact the IT administrator.
