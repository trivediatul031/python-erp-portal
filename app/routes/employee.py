from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from app.models import db, TASRecord, Employee
from app.forms import SubmitTASForm
from app.utils import generate_tas_number

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


def employee_required(f):
    """Decorator to require employee role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role != 'employee':
            flash('Access denied. Employee privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_active:
            flash('Your account is inactive. Please contact administrator.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.emp_id:
            flash('Your account is not linked to an employee record. Contact administrator.', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function


@employee_bp.route('/dashboard')
@login_required
@employee_required
def dashboard():
    """Employee dashboard"""
    employee = Employee.query.get(current_user.emp_id)
    
    # Get TAS statistics for this employee
    total_tas = TASRecord.query.filter_by(emp_id=current_user.emp_id).count()
    pending_tas = TASRecord.query.filter_by(emp_id=current_user.emp_id, status='Pending').count()
    approved_tas = TASRecord.query.filter_by(emp_id=current_user.emp_id, status='Approved').count()
    rejected_tas = TASRecord.query.filter_by(emp_id=current_user.emp_id, status='Rejected').count()
    
    # Get recent TAS submissions
    recent_tas = TASRecord.query.filter_by(
        emp_id=current_user.emp_id
    ).order_by(TASRecord.submitted_at.desc()).limit(5).all()
    
    return render_template(
        'employee/dashboard.html',
        employee=employee,
        total_tas=total_tas,
        pending_tas=pending_tas,
        approved_tas=approved_tas,
        rejected_tas=rejected_tas,
        recent_tas=recent_tas
    )


@employee_bp.route('/submit-tas', methods=['GET', 'POST'])
@login_required
@employee_required
def submit_tas():
    """Submit a new TAS request"""
    form = SubmitTASForm()
    
    if form.validate_on_submit():
        try:
            # Generate TAS number
            tas_number = generate_tas_number(current_user.emp_id)
            
            # Create TAS record
            tas = TASRecord(
                tas_number=tas_number,
                emp_id=current_user.emp_id,
                travel_from=form.travel_from.data,
                travel_to=form.travel_to.data,
                travel_date_start=form.travel_date_start.data,
                travel_date_end=form.travel_date_end.data,
                purpose=form.purpose.data,
                estimated_cost=form.estimated_cost.data,
                status='Pending',
                submitted_at=datetime.utcnow()
            )
            
            db.session.add(tas)
            db.session.commit()
            
            flash(f'TAS request submitted successfully! Your TAS number is: {tas_number}', 'success')
            return redirect(url_for('employee.tas_history'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting TAS request: {str(e)}', 'danger')
            return redirect(url_for('employee.submit_tas'))
    
    return render_template('employee/submit_tas.html', form=form)


@employee_bp.route('/tas-history')
@login_required
@employee_required
def tas_history():
    """View TAS submission history"""
    # Get filter parameter
    status_filter = request.args.get('status', '')
    
    # Build query
    query = TASRecord.query.filter_by(emp_id=current_user.emp_id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Get all TAS records for this employee
    tas_records = query.order_by(TASRecord.submitted_at.desc()).all()
    
    return render_template(
        'employee/tas_history.html',
        tas_records=tas_records,
        status_filter=status_filter
    )
