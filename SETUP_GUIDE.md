# TAS ERP Portal - Complete Setup Guide

## Quick Start (5 Minutes)

### Step 1: Install MySQL
Make sure MySQL is installed and running on your system.

### Step 2: Create Database
Open MySQL command line or MySQL Workbench and run:
```sql
CREATE DATABASE tas_erp;
```

### Step 3: Configure Database Connection
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` file with your MySQL credentials:
   ```
   DATABASE_URL=mysql+pymysql://root:YOUR_MYSQL_PASSWORD@localhost/tas_erp
   ```

### Step 4: Install Python Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Initialize Database
Run the schema SQL file:
```bash
mysql -u root -p tas_erp < schema.sql
```
Enter your MySQL password when prompted.

### Step 6: Start the Application
```bash
python run.py
```

### Step 7: Access the Portal
Open your browser and navigate to: **http://localhost:5000**

## Default Login Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin123`

## Testing the Portal

### Test 1: Admin Dashboard
1. Login with admin credentials
2. You should see the dashboard with statistics cards
3. All counts will be 0 initially (no TAS submissions yet)

### Test 2: Import Employees
1. Click "Import Employees" in the sidebar
2. Upload the `sample_employees.csv` file provided
3. Verify 5 employees are imported successfully

### Test 3: Create Employee User Account
Since employees need user accounts to login, you can create one manually:

```sql
-- Connect to database
mysql -u root -p tas_erp

-- Create user account for employee 1987 (John Doe)
INSERT INTO users (username, password_hash, role, emp_id, is_active)
VALUES ('john.doe', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7Plj3r9D4W', 'employee', '1987', TRUE);
```
Password for this account will be: `admin123` (same bcrypt hash)

### Test 4: Submit TAS as Employee
1. Logout from admin account
2. Login as employee: username `john.doe`, password `admin123`
3. Click "Submit TAS" from employee dashboard
4. Fill in travel details and submit
5. Verify TAS number is generated (TAS-1987-0001)

### Test 5: Approve TAS as Admin
1. Logout and login as admin
2. Go to "TAS Records"
3. Find the submitted TAS
4. Click "Approve" button
5. Verify status changes to "Approved"

## Dashboard Features

The admin dashboard displays:

### Statistics Cards (Top Row)
- **Purple Card**: Total TAS Submissions
- **Green Card**: Pending Approvals with percentage
- **Blue Card**: Approved count
- **Orange Card**: Rejected count with percentage

### Info Cards (Second Row)
- Employee database count
- Active employees count
- Quick action links
- Export data links

### Charts Section
- **Left**: Line chart showing TAS submissions over time (last 6 months)
- **Right**: Status mix panel with progress bars showing percentages

### Recent TAS Table
Shows the 10 most recent TAS submissions with:
- TAS number
- Employee name and ID
- Travel destination
- Travel dates
- Status badge
- Action buttons

## Common Issues & Solutions

### Issue 1: Cannot Connect to Database
**Error**: `OperationalError: (2003, "Can't connect to MySQL server")`

**Solution**:
- Verify MySQL service is running
- Check credentials in `.env` file
- Test connection: `mysql -u root -p`

### Issue 2: Import Failed
**Error**: Module 'pandas' not found

**Solution**:
```bash
pip install pandas openpyxl
```

### Issue 3: TAS Number Not Generating
**Error**: Sequence table error

**Solution**:
- Verify `tas_sequence` table exists
- Check foreign key constraints are enabled
- Ensure employee exists in database before TAS submission

### Issue 4: CSRF Token Missing
**Error**: CSRF validation failed

**Solution**:
- Clear browser cookies
- Restart the Flask application
- Verify `SECRET_KEY` is set in `.env`

## File Upload Limits

- Maximum file size: 10 MB
- Supported formats: CSV, XLSX, XLS
- Required columns for employee import: `emp_id`, `name`, `email`
- Optional columns: `department`, `designation`, `manager_id`

## Security Best Practices

### For Production Deployment:

1. **Change SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Use this value in `.env`

2. **Change Admin Password**:
   ```sql
   -- Generate new bcrypt hash with your desired password
   -- Use online bcrypt generator or Python:
   python -c "from flask_bcrypt import Bcrypt; print(Bcrypt().generate_password_hash('YOUR_NEW_PASSWORD').decode('utf-8'))"
   
   UPDATE users SET password_hash = 'NEW_HASH_HERE' WHERE username = 'admin';
   ```

3. **Set Flask Environment**:
   ```
   FLASK_ENV=production
   ```

4. **Use HTTPS**:
   - Configure reverse proxy (nginx/Apache)
   - Set `SESSION_COOKIE_SECURE = True` in config

5. **Database Security**:
   - Create dedicated database user (not root)
   - Grant only required privileges
   - Use strong password

## Troubleshooting Commands

### Check Database Tables
```bash
mysql -u root -p tas_erp -e "SHOW TABLES;"
```

### Check Employee Count
```bash
mysql -u root -p tas_erp -e "SELECT COUNT(*) FROM employees;"
```

### Check TAS Records
```bash
mysql -u root -p tas_erp -e "SELECT * FROM tas_records;"
```

### Reset Database (Caution!)
```bash
mysql -u root -p tas_erp < schema.sql
```
This will drop and recreate all tables!

## Development Tips

### Enable Debug Mode
Already enabled in `run.py`:
```python
app.run(debug=True)
```

### Auto-reload on Code Changes
Flask debug mode automatically reloads on file changes.

### Check Application Logs
All Flask logs appear in the terminal where you ran `python run.py`

## Support & Contact

For technical support or questions:
- Check the README.md file
- Review error logs in the terminal
- Contact IT administrator

## Next Steps

After successful setup:
1. Import your company's employee data
2. Create user accounts for employees
3. Customize email notifications (future feature)
4. Set up automated backups
5. Configure production deployment

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Tech Stack**: Flask 2.3, MySQL 8.0, Bootstrap 5.3
