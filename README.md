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

## Support

For issues or questions, contact the IT administrator.
