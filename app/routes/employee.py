from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from app.models import db, TASRecord, Employee, User
from app.forms import TASForm
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
    from flask import current_app
    form = TASForm()
    
    if form.validate_on_submit():
        try:
            # Validate emp_id
            if not current_user.emp_id:
                flash('Your account is not linked to an employee record. Contact admin.', 'error')
                return redirect(url_for('employee.dashboard'))
            
            # Get employee details
            employee = Employee.query.get(current_user.emp_id)
            if not employee:
                flash('Employee record not found. Contact admin.', 'error')
                return redirect(url_for('employee.dashboard'))
            
            # Generate TAS number (does not commit internally)
            tas_number = generate_tas_number(current_user.emp_id)
            
            # Use default values if fields are not provided
            travel_type = form.travel_type.data or 'Domestic'
            travel_mode = form.travel_mode.data or 'Air'
            purpose = form.purpose.data or 'Road Show'
            
            # Create TAS record
            tas = TASRecord(
                tas_number=tas_number,
                emp_id=current_user.emp_id,
                emp_name=employee.name,
                department=employee.department,
                travel_type=travel_type,
                travel_mode=travel_mode,
                travel_date_start=form.travel_date_start.data,
                purpose=purpose,
                status='Pending',
                submitted_at=datetime.now()
            )
            
            db.session.add(tas)
            # Commit both sequence update and TAS record atomically
            db.session.commit()
            
            flash(f'TAS submitted successfully. Your TAS number is {tas_number}', 'success')
            return redirect(url_for('employee.tas_history'))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error submitting TAS: {str(e)}', exc_info=True)
            flash('Failed to submit TAS. Please try again.', 'error')
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


@employee_bp.route('/tas/<int:tas_id>')
@login_required
@employee_required
def tas_detail(tas_id):
    """View TAS detail"""
    from flask import abort, current_app
    
    # Query TAS record
    tas_record = TASRecord.query.get(tas_id)
    
    if not tas_record:
        abort(404)
    
    # Validate ownership
    if tas_record.emp_id != current_user.emp_id:
        abort(403, 'You do not have permission to view this TAS')
    
    # Query reviewer info if reviewed
    reviewer_info = None
    if tas_record.reviewed_by:
        reviewer_user = User.query.get(tas_record.reviewed_by)
        if reviewer_user and reviewer_user.employee_profile:
            reviewer_info = {
                'name': reviewer_user.employee_profile.name,
                'username': reviewer_user.username
            }
        elif reviewer_user:
            reviewer_info = {
                'name': reviewer_user.username,
                'username': reviewer_user.username
            }
    
    return render_template('employee/tas_detail.html', 
                         tas_record=tas_record,
                         reviewer_info=reviewer_info)
