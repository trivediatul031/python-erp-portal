from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from sqlalchemy import Enum as SQLAEnum
from decimal import Decimal

db = SQLAlchemy()
bcrypt = Bcrypt()

class Employee(db.Model):
    __tablename__ = 'employees'
    
    emp_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    manager_id = db.Column(db.String(20), db.ForeignKey('employees.emp_id'))
    is_active = db.Column(db.Boolean)
    created_at = db.Column(db.TIMESTAMP)
    updated_at = db.Column(db.TIMESTAMP)
    
    # Relationships
    tas_records = db.relationship('TASRecord', back_populates='employee', lazy='dynamic')
    user = db.relationship('User', back_populates='employee_profile', uselist=False)
    
    def __repr__(self):
        return f'<Employee {self.emp_id}: {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'employee'
    emp_id = db.Column(db.String(20), db.ForeignKey('employees.emp_id'))
    is_active = db.Column(db.Boolean)
    created_at = db.Column(db.TIMESTAMP)
    updated_at = db.Column(db.TIMESTAMP)
    
    # Relationships
    employee_profile = db.relationship('Employee', back_populates='user')
    
    def set_password(self, password):
        """Hash and set the user's password. Validates min 8 characters."""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Return the user ID as a string for Flask-Login. Type-safe implementation."""
        if self.user_id is None:
            raise ValueError("User ID is None")
        return str(self.user_id)
    
    def __repr__(self):
        return f'<User {self.username}>'


class TASRecord(db.Model):
    __tablename__ = 'tas_records'
    
    tas_id = db.Column(db.Integer, primary_key=True)
    tas_number = db.Column(db.String(30), unique=True, nullable=False)
    emp_id = db.Column(db.String(20), db.ForeignKey('employees.emp_id'), nullable=False)
    travel_from = db.Column(db.String(255), nullable=False)
    travel_to = db.Column(db.String(255), nullable=False)
    travel_date_start = db.Column(db.Date, nullable=False)
    travel_date_end = db.Column(db.Date, nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    estimated_cost = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Approved', or 'Rejected'
    submitted_at = db.Column(db.TIMESTAMP)
    reviewed_at = db.Column(db.TIMESTAMP)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP)
    updated_at = db.Column(db.TIMESTAMP)
    
    # Relationships
    employee = db.relationship('Employee', back_populates='tas_records')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f'<TASRecord {self.tas_number}>'


class TASSequence(db.Model):
    __tablename__ = 'tas_sequence'
    
    emp_id = db.Column(db.String(20), db.ForeignKey('employees.emp_id'), primary_key=True)
    last_sequence = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<TASSequence {self.emp_id}: {self.last_sequence}>'
