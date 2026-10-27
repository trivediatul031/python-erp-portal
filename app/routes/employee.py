from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from app.models import db, TASRecord, Employee
from app.forms import TASForm
from app.utils import generate_tas_number

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


def employee_required(f):
    """Decorator to require employee role (admins also have access)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Allow both employees and admins to access
        if current_user.role not in ['employee', 'admin']:
            flash('Access denied. Employee privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function


@employee_bp.route('/dashboard')
@login_required
@employee_required
def dashboard():
    """Employee dashboard"""
    # Get TAS statistics for this employee
    total_tas = TASRecord.query.filter_by(emp_code=current_user.emp_code).count()
    
    # Get recent TAS submissions
    recent_tas = TASRecord.query.filter_by(
        emp_code=current_user.emp_code
    ).order_by(TASRecord.submitted_at.desc()).limit(5).all()
    
    return render_template(
        'employee/dashboard.html',
        total_tas=total_tas,
        recent_tas=recent_tas
    )


@employee_bp.route('/submit-tas', methods=['GET', 'POST'])
@login_required
def submit_tas():
    """Submit a new TR request - Available to all logged-in users"""
    from flask import current_app
    form = TASForm()
    
    if form.validate_on_submit():
        try:
            # Create TR record WITHOUT tas_number first (to get tas_id)
            tas = TASRecord(
                tas_number='TEMP',  # Temporary placeholder
                emp_code=current_user.emp_code,
                emp_name=current_user.name,
                department=current_user.organisation_unit,
                travel_date_start=form.travel_date_start.data,
                travel_type=None,
                travel_mode=None,
                purpose=None,
                status='Pending'
            )
            
            db.session.add(tas)
            db.session.flush()  # Get the tas_id without committing
            
            # Generate TR number using tas_id with 4-digit padding: TR-{emp_code}-{tas_id:04d}
            tas_number = f'TR-{current_user.emp_code}-{tas.tas_id:04d}'
            print(f"DEBUG: Generated TR number: {tas_number} for tas_id: {tas.tas_id}")
            tas.tas_number = tas_number
            
            db.session.commit()
            print(f"DEBUG: After commit, TR number: {tas.tas_number}")
            
            flash(f'TR submitted successfully. Your TR number is {tas_number}', 'success')
            return redirect(url_for('employee.tas_history'))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error submitting TR: {str(e)}', exc_info=True)
            flash('Failed to submit TR. Please try again.', 'error')
            return redirect(url_for('employee.submit_tas'))
    
    return render_template('employee/submit_tas.html', form=form)


@employee_bp.route('/tas-history')
@login_required
@employee_required
def tas_history():
    """View TR submission history"""
    # Get filter parameter
    status_filter = request.args.get('status', '')
    
    # Build query
    query = TASRecord.query.filter_by(emp_code=current_user.emp_code)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Get all TR records for this employee
    tas_records = query.order_by(TASRecord.submitted_at.desc()).all()
    
    return render_template(
        'employee/tas_history.html',
        tas_records=tas_records,
        status_filter=status_filter
    )


@employee_bp.route('/tas/<int:tas_id>')
@login_required
@employee_required
def tas_detail(tas_id):
    """View TR detail"""
    from flask import abort
    
    # Query TR record
    tas_record = TASRecord.query.get(tas_id)
    
    if not tas_record:
        abort(404)
    
    # Validate ownership
    if tas_record.emp_code != current_user.emp_code:
        abort(403, 'You do not have permission to view this TR')
    
    # Query reviewer info if reviewed
    reviewer_info = None
    if tas_record.reviewed_by:
        reviewer_emp = Employee.query.filter_by(emp_code=tas_record.reviewed_by).first()
        if reviewer_emp:
            reviewer_info = {
                'name': reviewer_emp.name,
                'emp_code': reviewer_emp.emp_code
            }
    
    return render_template('employee/tas_detail.html', 
                         tas_record=tas_record,
                         reviewer_info=reviewer_info)
