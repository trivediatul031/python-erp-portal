from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField, DecimalField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError, Optional, Regexp
from datetime import date

class LoginForm(FlaskForm):
    """Login form for user authentication."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class ImportEmployeesForm(FlaskForm):
    """Form for importing employees from Excel/CSV file."""
    file = FileField('Employee File', validators=[
        FileRequired(),
        FileAllowed(['csv', 'xlsx', 'xls'], 'Only CSV and Excel files are allowed!')
    ])
    submit = SubmitField('Import Employees')


class RejectTASForm(FlaskForm):
    """Form for rejecting TAS with reason."""
    rejection_reason = TextAreaField('Rejection Reason', validators=[
        DataRequired(),
        Length(min=10, max=500, message='Reason must be between 10 and 500 characters')
    ])
    submit = SubmitField('Reject TAS')


class SubmitTASForm(FlaskForm):
    """Form for employees to submit TAS requests."""
    travel_from = StringField('Travel From', validators=[
        DataRequired(),
        Length(max=255)
    ])
    travel_to = StringField('Travel To', validators=[
        DataRequired(),
        Length(max=255)
    ])
    travel_date_start = DateField('Start Date', validators=[DataRequired()])
    travel_date_end = DateField('End Date', validators=[DataRequired()])
    purpose = TextAreaField('Purpose of Travel', validators=[
        DataRequired(),
        Length(min=10, max=1000)
    ])
    estimated_cost = DecimalField('Estimated Cost', validators=[
        DataRequired(),
        NumberRange(min=0, max=9999999.99)
    ], places=2)
    submit = SubmitField('Submit TAS Request')
    
    def validate_travel_date_end(self, field):
        """Validate that end date is not before start date."""
        if self.travel_date_start.data and field.data:
            if field.data < self.travel_date_start.data:
                raise ValidationError('End date cannot be before start date')
    
    def validate_travel_date_start(self, field):
        """Validate that start date is not in the past."""
        if field.data and field.data < date.today():
            raise ValidationError('Start date cannot be in the past')


class CreateUserForm(FlaskForm):
    """Form for creating new users."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=50),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username must contain only letters, numbers, and underscores')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    role = SelectField('Role', choices=[
        ('admin', 'Admin'),
        ('employee', 'Employee')
    ], validators=[DataRequired()])
    emp_id = SelectField('Employee ID', coerce=lambda x: x or None, validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Create User')
    
    def validate_emp_id(self, field):
        """Validate that employee ID is provided for employee role."""
        if self.role.data == 'employee' and not field.data:
            raise ValidationError('Employee ID is required for employee role')

