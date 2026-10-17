"""Check current database status"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Employee

app = create_app()

with app.app_context():
    # Check employees
    employees = Employee.query.limit(5).all()
    print("Sample Employees:")
    for emp in employees:
        print(f"  - ID: {emp.emp_id}, Name: {emp.name}")
    
    print(f"\nTotal Employees: {Employee.query.count()}")
    
    # Check users
    users = User.query.limit(5).all()
    print("\nSample Users:")
    for user in users:
        print(f"  - Username: {user.username}, Emp ID: {user.emp_id}")
    
    print(f"\nTotal Users: {User.query.count()}")
