# Travel Approval System (TAS) - Deployment Guide

This guide provides step-by-step instructions for deploying the TAS ERP Portal to a production environment.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Deployment Options](#deployment-options)
4. [Database Setup](#database-setup)
5. [Running in Production](#running-in-production)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or Windows Server
- **Python**: 3.9 or higher
- **Database**: MySQL 8.0+ or PostgreSQL 13+ (SQLite for testing only)
- **RAM**: Minimum 2GB, 4GB recommended
- **Disk**: 10GB minimum

### Required Software
- Docker & Docker Compose (for containerized deployment)
- nginx (for reverse proxy)
- Git

---

## Environment Configuration

### 1. Generate Secret Key

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

Copy the output - this is your SECRET_KEY.

### 2. Create Environment File

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# Required Settings
FLASK_ENV=production
SECRET_KEY=<your-generated-secret-key>
DATABASE_URL=mysql+pymysql://tas_user:password@localhost:3306/tas_erp

# Database Passwords (for Docker)
DB_ROOT_PASSWORD=<strong-root-password>
DB_PASSWORD=<strong-db-password>

# Optional Settings
PORT=8000
GUNICORN_WORKERS=4
LOG_LEVEL=info
```

**Security Notes:**
- Never commit `.env` file to version control
- Use strong, unique passwords (minimum 16 characters)
- Rotate SECRET_KEY periodically
- Store backups of `.env` securely

---

## Deployment Options

### Option 1: Docker Deployment (Recommended)

Docker provides the easiest and most consistent deployment method.

#### 1.1. Build and Start Services

```bash
# Build the Docker image
docker-compose build

# Start all services (web app, database, nginx)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f web
```

#### 1.2. Initialize Database

```bash
# Access the web container
docker-compose exec web bash

# Inside the container, run Python shell
python
```

```python
from app import create_app, db
from app.models import User, Employee

app = create_app('production')
with app.app_context():
    db.create_all()
    print("Database initialized!")
```

#### 1.3. Create Admin User

```python
# Still in Python shell
admin = User(
    username='admin',
    role='admin',
    is_active=True
)
admin.set_password('your-secure-password')  # Change this!

db.session.add(admin)
db.session.commit()
print("Admin user created!")
```

#### 1.4. Access the Application

- **Via nginx**: http://your-server-ip (port 80)
- **Direct access**: http://your-server-ip:8000

---

### Option 2: Manual Deployment (Linux)

For deployment without Docker.

#### 2.1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv mysql-server nginx

# Install MySQL client libraries
sudo apt-get install -y default-libmysqlclient-dev build-essential
```

#### 2.2. Setup Application

```bash
# Clone repository
git clone <your-repo-url> /opt/tas_erp
cd /opt/tas_erp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
nano .env  # Edit with your settings
```

#### 2.3. Setup MySQL Database

```bash
# Login to MySQL
sudo mysql -u root -p

# Create database and user
CREATE DATABASE tas_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tas_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON tas_erp.* TO 'tas_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 2.4. Initialize Database

```bash
# Activate venv if not already active
source venv/bin/activate

# Run Python
python
```

```python
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
```

#### 2.5. Create Systemd Service

Create `/etc/systemd/system/tas-erp.service`:

```ini
[Unit]
Description=TAS ERP Portal
After=network.target mysql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/tas_erp
Environment="PATH=/opt/tas_erp/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/opt/tas_erp/venv/bin/gunicorn --config gunicorn.conf.py run:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGQUIT
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Set permissions
sudo chown -R www-data:www-data /opt/tas_erp
sudo chmod -R 755 /opt/tas_erp

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable tas-erp
sudo systemctl start tas-erp

# Check status
sudo systemctl status tas-erp
```

#### 2.6. Configure nginx

Create `/etc/nginx/sites-available/tas-erp`:

```nginx
# Copy the content from nginx.conf provided in the repository
# Update server_name with your domain
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/tas-erp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Database Setup

### Import Employee Data

```bash
# Access admin panel at http://your-server/admin/dashboard
# Login with admin credentials
# Navigate to Import Employees
# Upload your employee Excel/CSV file

# File format requirements:
# - emp_id, name, email, department, designation
# - First row must be headers
# - Supported formats: .csv, .xlsx, .xls
```

---

## Running in Production

### Start Services

**Docker:**
```bash
docker-compose up -d
```

**Manual:**
```bash
sudo systemctl start tas-erp
sudo systemctl start nginx
```

### Stop Services

**Docker:**
```bash
docker-compose down
```

**Manual:**
```bash
sudo systemctl stop tas-erp
sudo systemctl stop nginx
```

### View Logs

**Docker:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
```

**Manual:**
```bash
# Application logs
sudo journalctl -u tas-erp -f

# nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application file logs
tail -f /opt/tas_erp/logs/erpportal.log
```

---

## Monitoring & Maintenance

### Health Checks

Access the health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### Database Backup

```bash
# MySQL backup
mysqldump -u root -p tas_erp > backup_$(date +%Y%m%d).sql

# Restore
mysql -u root -p tas_erp < backup_20250118.sql
```

### Log Rotation

The application uses RotatingFileHandler (10MB per file, 10 backups).

For nginx logs, configure logrotate:

```bash
# /etc/logrotate.d/tas-erp
/var/log/nginx/tas-erp-*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

### Updates & Patches

```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart application
docker-compose restart web  # Docker
sudo systemctl restart tas-erp  # Manual
```

---

## Troubleshooting

### Application Won't Start

**Error**: `SECRET_KEY must be set in environment variables`

**Solution**: Ensure `.env` file exists with valid SECRET_KEY.

```bash
# Check environment
cat .env | grep SECRET_KEY

# Generate new key if needed
python -c 'import secrets; print(secrets.token_hex(32))'
```

---

### Database Connection Errors

**Error**: `Can't connect to MySQL server`

**Check database is running:**
```bash
# Docker
docker-compose ps db

# Manual
sudo systemctl status mysql
```

**Verify credentials:**
```bash
mysql -u tas_user -p tas_erp
```

---

### 502 Bad Gateway (nginx)

**Cause**: Gunicorn not running or wrong port

**Solution**:
```bash
# Check Gunicorn is running
curl http://localhost:8000/health

# Check nginx configuration
sudo nginx -t

# View nginx error log
sudo tail -f /var/log/nginx/error.log
```

---

### High Memory Usage

**Solution**: Reduce Gunicorn workers

Edit `.env`:
```bash
GUNICORN_WORKERS=2  # Reduce from 4
```

Or edit `gunicorn.conf.py`:
```python
workers = 2  # Adjust based on available RAM
```

---

### Rate Limiting Issues

If legitimate users are being rate-limited:

1. Check nginx logs for the affected IP
2. Adjust rate limits in `nginx.conf`
3. Consider implementing IP whitelist for admin IPs

---

## Security Checklist

Before going live:

- [ ] SECRET_KEY set and not using default value
- [ ] DEBUG = False in production
- [ ] Strong database passwords configured
- [ ] SSL certificates installed and HTTPS enabled
- [ ] Firewall configured (only ports 80, 443 open)
- [ ] Database only accessible from localhost
- [ ] Regular backups configured
- [ ] Log monitoring set up
- [ ] Admin password is strong and unique
- [ ] `.env` file not in version control
- [ ] Security headers verified (run: curl -I http://your-server)

---

## Support

For issues or questions:
1. Check logs first (application and nginx)
2. Review this troubleshooting guide
3. Check GitHub issues
4. Contact system administrator

---

**Last Updated**: January 2025
**Version**: 1.0.0
