from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from flask_login import current_user
from flask_wtf.csrf import csrf_exempt
from app.auth import admin_required
from app.models import db, Employee, TASRecord
from app.forms import ImportEmployeesForm
from werkzeug.utils import secure_filename
from sqlalchemy import func, cast, Date, extract, case
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
            Employee, TASRecord.emp_code == Employee.emp_code
        ).order_by(TASRecord.submitted_at.desc()).limit(10).all()
        
        # Check if admin is also an employee (current_user IS Employee now)
        admin_tas_records = []
        if current_user.emp_code:
            admin_tas_records = TASRecord.query.filter_by(
                emp_code=current_user.emp_code
            ).order_by(TASRecord.submitted_at.desc()).limit(5).all()
        
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
                             recent_tas=recent_tas,
                             admin_employee=current_user,
                             admin_tas_records=admin_tas_records)
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
                             recent_tas=[],
                             admin_employee=current_user,
                             admin_tas_records=[])


@admin_bp.route('/employee_list')
@admin_required
def employee_list():
    """View all employees with search and filter."""
    try:
        # Parse query params
        search = request.args.get('search', '').strip()
        organisation_unit = request.args.get('organisation_unit', '').strip()
        
        # Build query (no more user relationship)
        query = Employee.query
        
        # Apply filters
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (Employee.emp_code.like(search_pattern)) |
                (Employee.name.like(search_pattern)) |
                (Employee.email.like(search_pattern))
            )
        
        if organisation_unit:
            query = query.filter(Employee.organisation_unit == organisation_unit)
        
        # Get all employees
        employees = query.order_by(Employee.emp_code).all()
        
        # Get unique organisation units for filter dropdown
        organisation_units = db.session.query(Employee.organisation_unit).distinct().filter(
            Employee.organisation_unit.isnot(None)
        ).order_by(Employee.organisation_unit).all()
        organisation_units = [d[0] for d in organisation_units]
        
        return render_template('admin/employee_list.html',
                             employees=employees,
                             organisation_units=organisation_units,
                             search=search,
                             organisation_unit_filter=organisation_unit)
    except Exception as e:
        logger.error(f"Error loading employee list: {str(e)}", exc_info=True)
        flash('Error loading employee list', 'error')
        return render_template('admin/employee_list.html',
                             employees=[],
                             organisation_units=[],
                             search='',
                             organisation_unit_filter='')


def parse_date(date_str):
    """Parse date from dd/mm/yy or dd/mm/yyyy format"""
    from datetime import datetime
    import pandas as pd
    
    if pd.isna(date_str) or not date_str:
        return None
    
    date_str = str(date_str).strip()
    
    # Try multiple date formats
    formats = ['%d/%m/%y', '%d/%m/%Y', '%d-%m-%y', '%d-%m-%Y', '%Y-%m-%d']
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            continue
    
    return None


@admin_bp.route('/download_employee_template')
@admin_required
def download_employee_template():
    """Download the employee template CSV file."""
    template_path = os.path.join(current_app.root_path, '..', 'employee_template.csv')
    template_path = os.path.abspath(template_path)
    
    try:
        return send_file(template_path, as_attachment=True, download_name='employee_template.csv', mimetype='text/csv')
    except Exception as e:
        logger.error(f"Error downloading employee template: {str(e)}", exc_info=True)
        flash('Error downloading template file', 'error')
        return redirect(url_for('admin.import_employees'))


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
            required_columns = ['Emp. Code', 'Employee Name', 'Email ID']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
                return redirect(url_for('admin.import_employees'))
            
            # Validate row count
            if len(df) > 1000:
                flash('File contains more than 1000 rows. Please split the file.', 'error')
                return redirect(url_for('admin.import_employees'))
            
            # Validate no duplicate emp_code within file
            if df['Emp. Code'].duplicated().any():
                duplicate_ids = df[df['Emp. Code'].duplicated()]['Emp. Code'].tolist()
                flash(f'Duplicate Emp. Code found in file: {", ".join(map(str, duplicate_ids))}', 'error')
                return redirect(url_for('admin.import_employees'))
            
            # Validate no duplicate email within file
            if df['Email ID'].duplicated().any():
                duplicate_emails = df[df['Email ID'].duplicated()]['Email ID'].tolist()
                flash(f'Duplicate Email ID found in file: {", ".join(duplicate_emails)}', 'error')
                return redirect(url_for('admin.import_employees'))
            
            # Process rows with partial success
            success_count = 0
            error_rows = []
            
            for index, row in df.iterrows():
                try:
                    # Extract and validate required fields
                    emp_code = str(row.get('Emp. Code', '')).strip()
                    name = str(row.get('Employee Name', '')).strip()
                    email = str(row.get('Email ID', '')).strip().lower()
                    
                    if not emp_code or not name or not email:
                        error_rows.append((index + 2, 'Missing required data'))
                        continue
                    
                    if '@' not in email:
                        error_rows.append((index + 2, f'Invalid email: {email}'))
                        continue
                    
                    # Check if employee exists
                    employee = Employee.query.filter_by(emp_code=emp_code).first()
                    
                    if not employee:
                        # Create new employee
                        employee = Employee()
                        db.session.add(employee)
                    
                    # Set all fields
                    employee.emp_code = emp_code
                    employee.name = name
                    employee.email = email
                    
                    # Optional fields
                    employee.employment_category = str(row.get('Employment Category', '')).strip() or None
                    employee.doj = parse_date(row.get('DOJ (dd/mm/yy)'))
                    employee.designation = str(row.get('Current Designation', '')).strip() or None
                    employee.band = str(row.get('Current Band', '')).strip() or None
                    employee.organisation_unit = str(row.get('Organisation Unit Name', '')).strip() or None
                    employee.cluster = str(row.get('Cluster', '')).strip() or None
                    employee.team_name = str(row.get('Team Name', '')).strip() or None
                    employee.team_code = str(row.get('Team Code', '')).strip() or None
                    employee.reporting_manager = str(row.get('Reporting Manager', '')).strip() or None
                    employee.lead = str(row.get('Lead', '')).strip() or None
                    employee.hod = str(row.get('HOD', '')).strip() or None
                    employee.senior_leader = str(row.get('Senior Leader', '')).strip() or None
                    employee.is_active = True
                    
                    # Per-row commit
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
            TASRecord.emp_code,
            Employee.name,
            Employee.email,
            Employee.organisation_unit,
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
        ).join(Employee, TASRecord.emp_code == Employee.emp_code)
        
        # Apply filters
        if status != 'All':
            query = query.filter(TASRecord.status == status)
        
        if date_from_dt:
            query = query.filter(TASRecord.submitted_at >= date_from_dt)
        
        if date_to_dt:
            # FINDING #10: Include full day by adding 1 day and using < operator
            query = query.filter(TASRecord.submitted_at < date_to_dt + timedelta(days=1))
        
        if department:
            query = query.filter(Employee.organisation_unit == department)
        
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
    """View all TAS records with filters and optional grouping by employee."""
    try:
        # Parse query params
        view = request.args.get('view', 'all')
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        department = request.args.get('department', '')
        
        # Parse filter dates for query
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from)
            except ValueError:
                logger.warning(f"Invalid date_from format: {date_from}")
        
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to)
            except ValueError:
                logger.warning(f"Invalid date_to format: {date_to}")
        
        # Grouped view
        if view == 'grouped':
            # Build base query for aggregates
            query = db.session.query(
                Employee.emp_code,
                Employee.name,
                Employee.organisation_unit,
                func.count(TASRecord.tas_id).label('total'),
                func.sum(case((TASRecord.status == 'Pending', 1), else_=0)).label('pending'),
                func.sum(case((TASRecord.status == 'Approved', 1), else_=0)).label('approved'),
                func.sum(case((TASRecord.status == 'Rejected', 1), else_=0)).label('rejected')
            ).select_from(Employee).join(TASRecord, Employee.emp_code == TASRecord.emp_code)
            
            # Apply filters to aggregate query
            if status and status != 'All':
                query = query.filter(TASRecord.status == status)
            
            if date_from_dt:
                query = query.filter(TASRecord.submitted_at >= date_from_dt)
            
            if date_to_dt:
                # Include full day by adding 1 day
                query = query.filter(TASRecord.submitted_at < date_to_dt + timedelta(days=1))
            
            if department:
                query = query.filter(Employee.organisation_unit == department)
            
            # Group by employee
            query = query.group_by(Employee.emp_code, Employee.name, Employee.organisation_unit)
            
            # Execute aggregate query
            aggregate_results = query.all()
            
            # For each employee group, fetch their detailed TAS records
            grouped_data = []
            for agg in aggregate_results:
                # Build detail query with same filters
                detail_query = TASRecord.query.filter_by(emp_code=agg.emp_code)
                
                if status and status != 'All':
                    detail_query = detail_query.filter(TASRecord.status == status)
                
                if date_from_dt:
                    detail_query = detail_query.filter(TASRecord.submitted_at >= date_from_dt)
                
                if date_to_dt:
                    detail_query = detail_query.filter(TASRecord.submitted_at < date_to_dt + timedelta(days=1))
                
                detail_records = detail_query.order_by(TASRecord.submitted_at.desc()).all()
                
                grouped_data.append({
                    'emp_code': agg.emp_code,
                    'name': agg.name,
                    'organisation_unit': agg.organisation_unit,
                    'total': agg.total,
                    'pending': agg.pending,
                    'approved': agg.approved,
                    'rejected': agg.rejected,
                    'detail_records': detail_records
                })
            
            return render_template('admin/tas_list.html',
                                 view=view,
                                 grouped_data=grouped_data,
                                 results=None,
                                 status_filter=status,
                                 date_from=date_from,
                                 date_to=date_to,
                                 department=department)
        
        # All records view (default)
        else:
            # Build query with Employee join
            query = db.session.query(TASRecord, Employee).join(
                Employee, TASRecord.emp_code == Employee.emp_code
            )
            
            # Apply filters
            if status and status != 'All':
                query = query.filter(TASRecord.status == status)
            
            if date_from_dt:
                query = query.filter(TASRecord.submitted_at >= date_from_dt)
            
            if date_to_dt:
                # FINDING #10: Include full day by adding 1 day
                query = query.filter(TASRecord.submitted_at < date_to_dt + timedelta(days=1))
            
            if department:
                query = query.filter(Employee.organisation_unit == department)
            
            # Execute query
            results = query.order_by(TASRecord.submitted_at.desc()).all()
            
            return render_template('admin/tas_list.html',
                                 view=view,
                                 grouped_data=None,
                                 results=results,
                                 status_filter=status,
                                 date_from=date_from,
                                 date_to=date_to,
                                 department=department)
    except Exception as e:
        logger.error(f"Error loading TAS list: {str(e)}", exc_info=True)
        flash('Error loading TR list', 'error')
        return render_template('admin/tas_list.html',
                             view='all',
                             grouped_data=None,
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
            Employee, TASRecord.emp_code == Employee.emp_code
        ).filter(TASRecord.tas_id == tas_id).first()
        
        if not result:
            abort(404)
        
        tas_record, employee = result
        
        # Query reviewer info if reviewed
        reviewer_info = None
        if tas_record.reviewed_by:
            reviewer = Employee.query.filter_by(emp_code=tas_record.reviewed_by).first()
            if reviewer:
                reviewer_info = {
                    'name': reviewer.name,
                    'emp_code': reviewer.emp_code
                }
        
        return render_template('admin/tas_detail.html',
                             tas_record=tas_record,
                             employee=employee,
                             reviewer_info=reviewer_info)
    except Exception as e:
        logger.error(f"Error loading TAS detail: {str(e)}", exc_info=True)
        flash('Error loading TR detail', 'error')
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
        tas_record.reviewed_by = current_user.emp_code  # Changed to emp_code
        
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
        tas_record.reviewed_by = current_user.emp_code  # Changed to emp_code
        tas_record.rejection_reason = rejection_reason
        
        db.session.commit()
        
        flash('TR rejected', 'success')
        return redirect(url_for('admin.tas_detail', tas_id=tas_id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error rejecting TAS: {str(e)}', exc_info=True)
        flash('Error updating TR status', 'error')
        return redirect(url_for('admin.tas_detail', tas_id=tas_id))


@admin_bp.route('/user_management')
@admin_required
def user_management():
    """User management page listing all employees with their roles."""
    # Redirect to the new route
    return redirect(url_for('admin.role_management_v2'))


@admin_bp.route('/role_management')
@admin_required
def role_management_v2():
    """User management page listing all employees with their roles - V2."""
    try:
        # Parse query params
        search = request.args.get('search', '').strip()
        role_filter = request.args.get('role', '').strip()
        
        # Build query
        query = Employee.query
        
        # Apply filters
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (Employee.emp_code.like(search_pattern)) |
                (Employee.name.like(search_pattern)) |
                (Employee.email.like(search_pattern))
            )
        
        if role_filter and role_filter != 'All':
            query = query.filter(Employee.role == role_filter)
        
        # Get all employees with ordering
        employees = query.order_by(Employee.name).all()
        
        return render_template('admin/manage_roles.html', 
                             employees=employees)
    except Exception as e:
        logger.error(f"Error loading role management: {str(e)}", exc_info=True)
        flash('Error loading role management', 'error')
        return render_template('admin/manage_roles.html', 
                             employees=[])


@admin_bp.route('/promote_employee/<emp_code>', methods=['POST'])
@admin_required
def promote_employee(emp_code):
    """Promote employee to admin role with CSRF validation."""
    from flask import abort
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Manual CSRF validation
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    try:
        employee = Employee.query.filter_by(emp_code=emp_code).first()
        
        if not employee:
            abort(404)
        
        if employee.role == 'admin':
            flash('Employee is already an admin', 'warning')
        else:
            employee.role = 'admin'
            db.session.commit()
            flash(f'{employee.name} promoted to admin successfully', 'success')
        
        return redirect(url_for('admin.manage_roles'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error promoting employee: {str(e)}', exc_info=True)
        flash('Error updating employee role', 'error')
        return redirect(url_for('admin.manage_roles'))


@admin_bp.route('/demote_employee/<emp_code>', methods=['POST'])
@admin_required
def demote_employee(emp_code):
    """Demote employee to employee role with CSRF validation."""
    from flask import abort
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Manual CSRF validation
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    try:
        employee = Employee.query.filter_by(emp_code=emp_code).first()
        
        if not employee:
            abort(404)
        
        if employee.role == 'employee':
            flash('Employee already has employee role', 'warning')
        else:
            employee.role = 'employee'
            db.session.commit()
            flash(f'{employee.name} changed to employee role successfully', 'success')
        
        return redirect(url_for('admin.manage_roles'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error demoting employee: {str(e)}', exc_info=True)
        flash('Error updating employee role', 'error')
        return redirect(url_for('admin.manage_roles'))

        
        return render_template('admin/user_management.html',
                             employees=employees,
                             search=search,
                             role_filter=role_filter)
    except Exception as e:
        logger.error(f"Error loading user management: {str(e)}", exc_info=True)
        flash('Error loading user management', 'error')
        return render_template('admin/user_management.html',
                             employees=[],
                             search='',
                             role_filter='')


@admin_bp.route('/update_role/<emp_code>', methods=['POST'])
@csrf_exempt
@admin_required
def update_role(emp_code):
    """Update employee role via AJAX."""
    try:
        # Get the new role from request
        data = request.get_json()
        new_role = data.get('role', '').strip()
        
        # Validate role
        if new_role not in ['employee', 'admin']:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
        
        # Find employee
        employee = Employee.query.filter_by(emp_code=emp_code).first()
        if not employee:
            return jsonify({'success': False, 'message': 'Employee not found'}), 404
        
        # Update role
        old_role = employee.role
        employee.role = new_role
        db.session.commit()
        
        logger.info(f"Role updated for {emp_code} ({employee.name}) from {old_role} to {new_role} by {current_user.emp_code}")
        
        return jsonify({
            'success': True, 
            'message': f'Role updated to {new_role}',
            'new_role': new_role,
            'employee_name': employee.name
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating role for {emp_code}: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
