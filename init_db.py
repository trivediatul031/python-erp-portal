#!/usr/bin/env python3
"""
Initialize database with tables and indexes.
Run this script once to set up the database.
"""
import os
os.environ['FLASK_ENV'] = 'development'

from app import create_app, db
from app.models import Employee, User, TASRecord, TASSequence
from flask_bcrypt import Bcrypt
import sqlite3

bcrypt_instance = Bcrypt()

app = create_app()

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("✓ Tables created successfully")
    
    # Create the email index using raw SQL
    print("\nCreating case-insensitive email index...")
    try:
        db.session.execute(db.text("""
            CREATE INDEX IF NOT EXISTS idx_employee_email_lower 
            ON employees(LOWER(email));
        """))
        db.session.commit()
        print("✓ Email index created successfully")
    except Exception as e:
        print(f"✗ Error creating index: {e}")
        db.session.rollback()
    
    # Check if admin employee exists, create if not
    admin_emp = Employee.query.filter_by(emp_id='ADMIN').first()
    if not admin_emp:
        print("\nCreating admin employee record...")
        admin_emp = Employee(
            emp_id='ADMIN',
            name='System Administrator',
            email='admin@tas-erp.com',
            department='IT',
            designation='Administrator',
            is_active=True
        )
        db.session.add(admin_emp)
        db.session.commit()
        print("✓ Admin employee created")
    else:
        print("\n✓ Admin employee already exists")
    
    # Check if admin user exists, create if not
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("Creating admin user...")
        # Hash for 'admin123'
        password_hash = bcrypt_instance.generate_password_hash('admin123').decode('utf-8')
        admin_user = User(
            username='admin',
            password_hash=password_hash,
            role='admin',
            emp_id='ADMIN',
            is_active=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✓ Admin user created (username: admin, password: admin123)")
    else:
        print("✓ Admin user already exists")
    
    print("\n✓ Database initialization complete!")
    print("\nYou can now:")
    print("  1. Run 'python verify_index.py' to verify the email index")
    print("  2. Start the application with 'flask run'")
