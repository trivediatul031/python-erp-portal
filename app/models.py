from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from sqlalchemy import Enum as SQLAEnum
from decimal import Decimal

db = SQLAlchemy()
bcrypt = Bcrypt()

class Employee(UserMixin, db.Model):
    __tablename__ = 'employees'
    
    # Auto-increment primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Employee data from CSV
    emp_code = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Emp. Code from CSV
    employment_category = db.Column(db.String(100))  # Employment Category
    name = db.Column(db.String(200), nullable=False)  # Employee Name
    doj = db.Column(db.Date)  # Date of Joining
    designation = db.Column(db.String(150))  # Current Designation
    band = db.Column(db.String(50))  # Current Band
    organisation_unit = db.Column(db.String(200))  # Organisation Unit Name
    cluster = db.Column(db.String(200))  # Cluster
    team_name = db.Column(db.String(200))  # Team Name
    team_code = db.Column(db.String(50))  # Team Code
    reporting_manager = db.Column(db.String(200))  # Reporting Manager
    lead = db.Column(db.String(200))  # Lead
    hod = db.Column(db.String(200))  # HOD
    senior_leader = db.Column(db.String(200))  # Senior Leader
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)  # Email ID
    
    # Authentication fields (SSO-based, password_hash unused but kept for compatibility)
    role = db.Column(db.String(20), nullable=False, default='employee', index=True)  # 'admin' or 'employee'
    password_hash = db.Column(db.String(255), nullable=True)  # Unused for SSO, kept for compatibility
    
    # System fields
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relationships (using emp_code instead of emp_id for compatibility)
    tas_records = db.relationship('TASRecord', back_populates='employee', lazy='dynamic', foreign_keys='TASRecord.emp_code')
    
    def __repr__(self):
        return f'<Employee {self.emp_code}: {self.name}>'
    
    def get_id(self):
        """Return emp_code as string for Flask-Login"""
        return str(self.emp_code)
    
    def is_admin(self):
        """Check if employee has admin role"""
        return self.role == 'admin'
    
    def set_password(self, password):
        """Hash and set password (unused for SSO, kept for compatibility)"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check password (unused for SSO, kept for compatibility)"""
        if not self.password_hash:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)
    
    # For backward compatibility with old emp_id references
    @property
    def emp_id(self):
        """Alias for emp_code to maintain backward compatibility"""
        return self.emp_code
    
    @property  
    def department(self):
        """Alias for organisation_unit to maintain backward compatibility"""
        return self.organisation_unit



class TASRecord(db.Model):
    __tablename__ = 'tas_records'
    
    tas_id = db.Column(db.Integer, primary_key=True)
    tas_number = db.Column(db.String(30), unique=True, nullable=False)
    emp_code = db.Column(db.String(50), db.ForeignKey('employees.emp_code'), nullable=False)  # Changed from emp_id
    emp_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    # Legacy fields - no longer used for new TRs
    travel_type = db.Column(db.String(20), nullable=True)  # 'Domestic' or 'International'
    travel_mode = db.Column(db.String(20), nullable=True)  # 'Air', 'Rail', 'Road', etc.
    purpose = db.Column(db.String(100), nullable=True)
    travel_date_start = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Approved', or 'Rejected'
    submitted_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    reviewed_at = db.Column(db.TIMESTAMP)
    reviewed_by = db.Column(db.String(50), db.ForeignKey('employees.emp_code'))  # Changed to emp_code FK
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    employee = db.relationship('Employee', back_populates='tas_records', foreign_keys=[emp_code])
    reviewer = db.relationship('Employee', foreign_keys=[reviewed_by])  # Changed to Employee
    
    # Backward compatibility
    @property
    def emp_id(self):
        """Alias for emp_code to maintain backward compatibility"""
        return self.emp_code
    
    def __repr__(self):
        return f'<TASRecord {self.tas_number}>'

