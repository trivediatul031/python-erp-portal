from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from flask_login import current_user
from app.auth import admin_required
from app.models import db, Employee, User, TASRecord
from app.forms import ImportEmployeesForm, CreateUserForm
from werkzeug.utils import secure_filename
from sqlalchemy import func, cast, Date, extract
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import os
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with statistics and charts."""
    try:
        # Total TAS count
        total_tas = TASRecord.query.count()
        
        # Total Employees count
        total_employees = Employee.query.count()
        
        # Pending count
        pending_count = TASRecord.query.filter_by(status='Pending').count()
        
        # Approved this month (submitted_at >= first day of current month)
        first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        approved_this_month = TASRecord.query.filter(
            TASRecord.status == 'Approved',
            TASRecord.submitted_at >= first_day_of_month
        ).count()
        
        # Rejected count and rejection rate
        rejected_count = TASRecord.query.filter_by(status='Rejected').count()
        rejection_rate = round((rejected_count / total_tas * 100) if total_tas > 0 else 0, 1)
        
        # TAS submissions by date for last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        submissions_by_date = db.session.query(
            cast(TASRecord.submitted_at, Date).label('date'),
            func.count(TASRecord.tas_id).label('count')
        ).filter(
            TASRecord.submitted_at >= seven_days_ago
        ).group_by(
            cast(TASRecord.submitted_at, Date)
        ).order_by('date').all()
        
        # Format for Chart.js
        chart_dates = [str(row.date) for row in submissions_by_date]
        chart_counts = [row.count for row in submissions_by_date]
        
        # Status breakdown counts
        status_breakdown = {
            'Pending': pending_count,
            'Approved': TASRecord.query.filter_by(status='Approved').count(),
            'Rejected': rejected_count
        }
        
        # 10 most recent TAS with employee join
        recent_tas = db.session.query(TASRecord, Employee).join(
            Employee, TASRecord.emp_id == Employee.emp_id
        ).order_by(TASRecord.submitted_at.desc()).limit(10).all()
        
        return render_template('admin/dashboard.html',
                             total_tas=total_tas,
                             total_employees=total_employees,
                             pending_count=pending_count,
                             approved_this_month=approved_this_month,
                             rejected_count=rejected_count,
                             rejection_rate=rejection_rate,
                             chart_dates=chart_dates,
                             chart_counts=chart_counts,
                             status_breakdown=status_breakdown,
                             recent_tas=recent_tas)
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}", exc_info=True)
        flash('Error loading dashboard', 'error')
        return render_template('admin/dashboard.html',
                             total_tas=0,
                             total_employees=0,
                             pending_count=0,
                             approved_this_month=0,
                             rejected_count=0,
                             rejection_rate=0,
                             chart_dates=[],
                             chart_counts=[],
                             status_breakdown={'Pending': 0, 'Approved': 0, 'Rejected': 0},
                             recent_tas=[])


@admin_bp.route('/employee_list')
@admin_required
def employee_list():
    """View all employees with search and filter."""
    try:
        # Parse query params
        search = request.args.get('search', '').strip()
        department = request.args.get('department', '').strip()
        
        # Build query with user relationship
        query = Employee.query.options(db.joinedload(Employee.user))
        
        # Apply filters
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (Employee.emp_id.like(search_pattern)) |
                (Employee.name.like(search_pattern)) |
                (Employee.email.like(search_pattern))
            )
        
        if department:
            query = query.filter(Employee.department == department)
        
        # Get all employees
        employees = query.order_by(Employee.emp_id).all()
        
        # Get unique departments for filter dropdown
        departments = db.session.query(Employee.department).distinct().filter(
            Employee.department.isnot(None)
        ).order_by(Employee.department).all()
        departments = [d[0] for d in departments]
        
        return render_template('admin/employee_list.html',
                             employees=employees,
                             departments=departments,
                             search=search,
                             department_filter=department)
    except Exception as e:
        logger.error(f"Error loading employee list: {str(e)}", exc_info=True)
        flash('Error loading employee list', 'error')
        return render_template('admin/employee_list.html',
                             employees=[],
                             departments=[],
                             search='',
                             department_filter='')


@admin_bp.route('/import_employees', methods=['GET', 'POST'])
@admin_required
def import_employees():
    """Import employees from Excel/CSV file."""
    import pandas as pd
    
    form = ImportEmployeesForm()
    
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        try:
            # Save file
            file.save(filepath)
            
            # Read file based on extension
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(filepath)
            elif filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                flash('Invalid file format. Only .xlsx, .xls, and .csv are allowed.', 'error')
                return redirect(url_for('admin.import_employees'))
            
            # Validate required columns
            required_columns = ['emp_id', 'name', 'email']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
                return redirect(url_for('admin.import_employees'))
            
            # Validate row count
            if len(df) > 1000:
                flash('File contains more than 1000 rows. Please split the file.', 'error')
                return redirect(url_for('admin.import_employees'))
            
            # Validate no duplicate emp_id within file
            if df['emp_id'].duplicated().any():
                duplicate_ids = df[df['emp_id'].duplicated()]['emp_id'].tolist()
                flash(f'Duplicate emp_id found in file: {", ".join(map(str, duplicate_ids))}', 'error')
                return redirect(url_for('admin.import_employees'))
            
            # Validate no duplicate email within file
            if df['email'].duplicated().any():
                duplicate_emails = df[df['email'].duplicated()]['email'].tolist()
                flash(f'Duplicate email found in file: {", ".join(duplicate_emails)}', 'error')
                return redirect(url_for('admin.import_employees'))
            
            # Process rows with partial success
            success_count = 0
            error_rows = []
            
            for index, row in df.iterrows():
                try:
                    # Validate emp_id
                    emp_id = str(row['emp_id']).strip() if pd.notna(row['emp_id']) else ''
                    if not emp_id or len(emp_id) > 20:
                        error_rows.append((index + 2, 'Invalid emp_id'))
                        continue
                    
                    # Validate name
                    name = str(row['name']).strip() if pd.notna(row['name']) else ''
                    if not name or len(name) > 255:
                        error_rows.append((index + 2, 'Invalid name'))
                        continue
                    
                    # Validate email
                    email = str(row['email']).strip() if pd.notna(row['email']) else ''
                    if not email or len(email) > 255 or '@' not in email:
                        error_rows.append((index + 2, 'Invalid email'))
                        continue
                    
                    # Parse department and designation
                    department = str(row['department']).strip() if 'department' in row and pd.notna(row['department']) else None
                    designation = str(row['designation']).strip() if 'designation' in row and pd.notna(row['designation']) else None
                    
                    # Parse manager_id with null handling (FINDING #9)
                    manager_id = None
                    if 'manager_id' in row:
                        manager_id_raw = row['manager_id']
                        if pd.notna(manager_id_raw):
                            manager_id = str(manager_id_raw).strip()
                            if manager_id.lower() in ['', 'none', 'null', 'n/a', 'na']:
                                manager_id = None
                    
                    # Validate manager_id != emp_id
                    if manager_id and manager_id == emp_id:
                        error_rows.append((index + 2, 'manager_id cannot be same as emp_id'))
                        continue
                    
                    # Detect simple two-way circular reference
                    if manager_id and manager_id in df['emp_id'].values:
                        manager_row = df[df['emp_id'] == manager_id].iloc[0]
                        if 'manager_id' in manager_row and pd.notna(manager_row['manager_id']):
                            if str(manager_row['manager_id']).strip() == emp_id:
                                error_rows.append((index + 2, 'Circular reference detected with manager'))
                                continue
                    
                    # Create or update Employee
                    employee = Employee.query.filter_by(emp_id=emp_id).first()
                    if employee:
                        # Update existing
                        employee.name = name
                        employee.email = email
                        employee.department = department
                        employee.designation = designation
                        employee.manager_id = manager_id
                    else:
                        # Create new
                        employee = Employee(
                            emp_id=emp_id,
                            name=name,
                            email=email,
                            department=department,
                            designation=designation,
                            manager_id=manager_id
                        )
                        db.session.add(employee)
                    
                    # Per-row commit (FINDING #7)
                    db.session.commit()
                    success_count += 1
                    
                except IntegrityError as e:
                    db.session.rollback()
                    error_rows.append((index + 2, f'Database error: {str(e)}'))
                    logger.error(f"IntegrityError importing row {index + 2}: {str(e)}", exc_info=True)
                except Exception as e:
                    db.session.rollback()
                    error_rows.append((index + 2, str(e)))
                    logger.error(f"Error importing row {index + 2}: {str(e)}", exc_info=True)
            
            # Flash success and errors
            if success_count > 0:
                flash(f'Successfully imported {success_count} employees', 'success')
            
            if error_rows:
                error_messages = [f'Row {row}: {error}' for row, error in error_rows[:10]]
                if len(error_rows) > 10:
                    error_messages.append(f'... and {len(error_rows) - 10} more errors')
                flash('Errors: ' + '; '.join(error_messages), 'warning')
            
        except Exception as e:
            logger.error(f"Error processing import file: {str(e)}", exc_info=True)
            flash(f'Error processing file: {str(e)}', 'error')
        finally:
            # Cleanup temp file
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                logger.warning(f"Could not delete temp file {filepath}: {str(e)}")
        
        return redirect(url_for('admin.import_employees'))
    
    return render_template('admin/import_employees.html', form=form)


@admin_bp.route('/user_management')
@admin_required
def user_management():
    """User management page."""
    try:
        # Query all users with LEFT JOIN employee
        users = db.session.query(User, Employee).outerjoin(
            Employee, User.emp_id == Employee.emp_id
        ).all()
        
        return render_template('admin/user_management.html', users=users)
    except Exception as e:
        logger.error(f"Error loading user management: {str(e)}", exc_info=True)
        flash('Error loading user management', 'error')
        return render_template('admin/user_management.html', users=[])


@admin_bp.route('/create_user', methods=['GET', 'POST'])
@admin_required
def create_user():
    """Create new user."""
    form = CreateUserForm()
    
    # Populate emp_id choices with employees not linked to any user
    employees_not_linked = db.session.query(Employee).outerjoin(User).filter(
        User.user_id == None
    ).all()
    
    form.emp_id.choices = [('', 'None (for admin users)')] + [
        (emp.emp_id, f'{emp.name} ({emp.emp_id})') for emp in employees_not_linked
    ]
    
    if form.validate_on_submit():
        try:
            username = form.username.data
            password = form.password.data
            role = form.role.data
            emp_id = form.emp_id.data if form.emp_id.data else None
            is_active = form.is_active.data
            
            # Additional validation: employee role requires emp_id
            if role == 'employee' and not emp_id:
                flash('Employee ID is required for employee role', 'error')
                return render_template('admin/create_user.html', form=form)
            
            # Check emp_id not already linked
            if emp_id:
                existing_user = User.query.filter_by(emp_id=emp_id).first()
                if existing_user:
                    flash('This employee already has a user account', 'error')
                    return render_template('admin/create_user.html', form=form)
            
            # Create user
            user = User(
                username=username,
                role=role,
                emp_id=emp_id,
                is_active=is_active
            )
            
            # Set password (validates min 8 chars)
            try:
                user.set_password(password)
            except ValueError as e:
                flash(str(e), 'error')
                return render_template('admin/create_user.html', form=form)
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'User {username} created successfully', 'success')
            return redirect(url_for('admin.user_management'))
            
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"IntegrityError creating user: {str(e)}", exc_info=True)
            if 'username' in str(e):
                flash('Username already exists', 'error')
            else:
                flash('Database error: duplicate entry', 'error')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('admin/create_user.html', form=form)


@admin_bp.route('/export_tas')
@admin_required
def export_tas():
    """Export TAS records with filters."""
    import pandas as pd
    
    try:
        # Parse query params
        format_type = request.args.get('format', 'xlsx')
        status = request.args.get('status', 'All')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        department = request.args.get('department')
        
        # Validate dates
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from)
            except ValueError:
                return jsonify({'error': 'Invalid date_from format'}), 400
        else:
            date_from_dt = None
        
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to)
            except ValueError:
                return jsonify({'error': 'Invalid date_to format'}), 400
        else:
            date_to_dt = None
        
        if date_from_dt and date_to_dt and date_from_dt > date_to_dt:
            return jsonify({'error': 'date_from must be before date_to'}), 400
        
        # Build query
        query = db.session.query(
            TASRecord.tas_number,
            TASRecord.emp_id,
            Employee.name,
            Employee.email,
            Employee.department,
            Employee.designation,
            TASRecord.travel_from,
            TASRecord.travel_to,
            TASRecord.travel_date_start,
            TASRecord.travel_date_end,
            TASRecord.purpose,
            TASRecord.estimated_cost,
            TASRecord.status,
            TASRecord.submitted_at,
            TASRecord.reviewed_at
        ).join(Employee, TASRecord.emp_id == Employee.emp_id)
        
        # Apply filters
        if status != 'All':
            query = query.filter(TASRecord.status == status)
        
        if date_from_dt:
            query = query.filter(TASRecord.submitted_at >= date_from_dt)
        
        if date_to_dt:
            # FINDING #10: Include full day by adding 1 day and using < operator
            query = query.filter(TASRecord.submitted_at < date_to_dt + timedelta(days=1))
        
        if department:
            query = query.filter(Employee.department == department)
        
        # Execute query
        results = query.all()
        
        # Handle empty results (FINDING #8)
        columns = ['TAS Number', 'Employee ID', 'Employee Name', 'Email', 'Department', 
                  'Designation', 'From', 'To', 'Start Date', 'End Date', 'Purpose', 
                  'Estimated Cost', 'Status', 'Submitted At', 'Reviewed At']
        
        if not results:
            df = pd.DataFrame(columns=columns)
        else:
            df = pd.DataFrame(results, columns=columns)
        
        # Generate timestamp filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'tas_records_{timestamp}.{format_type}'
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        if format_type == 'csv':
            df.to_csv(filepath, index=False)
            mimetype = 'text/csv'
        else:
            df.to_excel(filepath, index=False, engine='openpyxl')
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        # Define cleanup function
        def cleanup_file():
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"Cleaned up export file: {filename}")
            except Exception as e:
                logger.warning(f"Could not delete export file {filepath}: {str(e)}")
        
        # Send file with cleanup
        response = send_file(filepath, as_attachment=True, download_name=filename, mimetype=mimetype)
        response.call_on_close(cleanup_file)
        return response
        
    except Exception as e:
        logger.error(f"Error exporting TAS records: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/tas_list')
@admin_required
def tas_list():
    """View all TAS records with filters."""
    try:
        # Parse query params
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        department = request.args.get('department', '')
        
        # Build query with Employee join
        query = db.session.query(TASRecord, Employee).join(
            Employee, TASRecord.emp_id == Employee.emp_id
        )
        
        # Apply filters
        if status and status != 'All':
            query = query.filter(TASRecord.status == status)
        
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from)
                query = query.filter(TASRecord.submitted_at >= date_from_dt)
            except ValueError:
                logger.warning(f"Invalid date_from format: {date_from}")
        
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to)
                # FINDING #10: Include full day by adding 1 day
                query = query.filter(TASRecord.submitted_at < date_to_dt + timedelta(days=1))
            except ValueError:
                logger.warning(f"Invalid date_to format: {date_to}")
        
        if department:
            query = query.filter(Employee.department == department)
        
        # Execute query
        results = query.order_by(TASRecord.submitted_at.desc()).all()
        
        return render_template('admin/tas_list.html',
                             results=results,
                             status_filter=status,
                             date_from=date_from,
                             date_to=date_to,
                             department=department)
    except Exception as e:
        logger.error(f"Error loading TAS list: {str(e)}", exc_info=True)
        flash('Error loading TAS list', 'error')
        return render_template('admin/tas_list.html',
                             results=[],
                             status_filter='',
                             date_from='',
                             date_to='',
                             department='')


@admin_bp.route('/tas/<int:tas_id>')
@admin_required
def tas_detail(tas_id):
    """View TAS detail with employee info and approval actions."""
    from flask import abort
    
    try:
        # Query TAS record with employee join
        result = db.session.query(TASRecord, Employee).join(
            Employee, TASRecord.emp_id == Employee.emp_id
        ).filter(TASRecord.tas_id == tas_id).first()
        
        if not result:
            abort(404)
        
        tas_record, employee = result
        
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
        
        return render_template('admin/tas_detail.html',
                             tas_record=tas_record,
                             employee=employee,
                             reviewer_info=reviewer_info)
    except Exception as e:
        logger.error(f"Error loading TAS detail: {str(e)}", exc_info=True)
        flash('Error loading TAS detail', 'error')
        return redirect(url_for('admin.tas_list'))


@admin_bp.route('/tas/<int:tas_id>/approve', methods=['POST'])
@admin_required
def approve_tas(tas_id):
    """Approve a TAS request with manual CSRF validation (FINDING #2)."""
    from flask import abort
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Manual CSRF validation
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    try:
        # Query TAS record
        tas_record = TASRecord.query.get(tas_id)
        
        if not tas_record:
            abort(404)
        
        # Check if already processed
        if tas_record.status != 'Pending':
            flash('TR has already been processed', 'warning')
            return redirect(url_for('admin.tas_detail', tas_id=tas_id))
        
        # Update TAS record
        tas_record.status = 'Approved'
        tas_record.reviewed_at = datetime.utcnow()
        tas_record.reviewed_by = current_user.user_id
        
        db.session.commit()
        
        flash('TR approved successfully', 'success')
        return redirect(url_for('admin.tas_detail', tas_id=tas_id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error approving TAS: {str(e)}', exc_info=True)
        flash('Error updating TR status', 'error')
        return redirect(url_for('admin.tas_detail', tas_id=tas_id))


@admin_bp.route('/tas/<int:tas_id>/reject', methods=['POST'])
@admin_required
def reject_tas(tas_id):
    """Reject a TAS request with manual CSRF validation (FINDING #2)."""
    from flask import abort
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Manual CSRF validation
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    try:
        # Query TAS record
        tas_record = TASRecord.query.get(tas_id)
        
        if not tas_record:
            abort(404)
        
        # Check if already processed
        if tas_record.status != 'Pending':
            flash('TR has already been processed', 'warning')
            return redirect(url_for('admin.tas_detail', tas_id=tas_id))
        
        # Get rejection reason (limit to 500 chars)
        rejection_reason = request.form.get('rejection_reason', '').strip()[:500]
        
        # Update TAS record
        tas_record.status = 'Rejected'
        tas_record.reviewed_at = datetime.utcnow()
        tas_record.reviewed_by = current_user.user_id
        tas_record.rejection_reason = rejection_reason
        
        db.session.commit()
        
        flash('TR rejected', 'success')
        return redirect(url_for('admin.tas_detail', tas_id=tas_id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error rejecting TAS: {str(e)}', exc_info=True)
        flash('Error updating TR status', 'error')
        return redirect(url_for('admin.tas_detail', tas_id=tas_id))
