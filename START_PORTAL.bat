@echo off
echo ========================================
echo TAS ERP Portal - Quick Start
echo ========================================
echo.

echo Step 1: Installing required packages...
pip install Flask==2.3.3 SQLAlchemy==2.0.20 Flask-Login==0.6.2 Flask-WTF==1.1.1 Flask-Bcrypt==1.0.1 pandas==2.1.0 openpyxl==3.1.2 python-dotenv==1.0.0 Werkzeug==2.3.7

echo.
echo Step 2: Creating database...
python init_db.py

echo.
echo Step 3: Starting Flask application...
echo.
echo Portal will be available at: http://localhost:5000
echo Login: admin / admin123
echo.
echo Press Ctrl+C to stop the server
echo.

python run.py

pause
