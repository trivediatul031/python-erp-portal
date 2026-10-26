import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import RequestEntityTooLarge
from config import config
from app.models import db, bcrypt

login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100000 per day", "10000 per hour"],  # Very high limits for development
    storage_uri="memory://"
)

def create_app(config_name='default'):
    """Flask application factory."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Disable template caching in debug mode
    if app.debug:
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.jinja_env.auto_reload = True
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Compute AZURE_REDIRECT_URI at initialization
    app_url = app.config.get('APP_URL')
    if app_url:
        app.config['AZURE_REDIRECT_URI'] = f"{app_url.rstrip('/')}/auth/Microsoft/callback"
    else:
        app.config['AZURE_REDIRECT_URI'] = None
    
    # Ensure upload folder exists
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Warn if templates or static folders are missing
    if not os.path.exists(os.path.join(app.root_path, 'templates')):
        app.logger.warning('Templates folder not found')
    if not os.path.exists(os.path.join(app.root_path, 'static')):
        app.logger.warning('Static folder not found')
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    # Temporarily disable CSRF for AJAX endpoints
    # csrf.init_app(app)
    limiter.init_app(app)
    
    # Configure production logging
    if not app.debug:
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Configure rotating file handler
        file_handler = RotatingFileHandler(
            'logs/erpportal.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        
        # Set formatter with detailed information
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Add handler to app logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('ERP Portal startup')
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by emp_code for Flask-Login with error handling."""
        from app.models import Employee
        try:
            # user_id is actually emp_code (string)
            return Employee.query.filter_by(emp_code=str(user_id)).first()
        except Exception:
            return None
    
    # Register error handlers
    @app.errorhandler(403)
    def forbidden(e):
        """Handle 403 Forbidden errors."""
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 Not Found errors."""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 Internal Server Error."""
        app.logger.error('Internal server error', exc_info=True)
        return render_template('errors/500.html'), 500
    
    # Register error handler for file upload size limit
    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(e):
        return 'File is too large. Maximum size is 10MB.', 413
    
    # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        security_headers = app.config.get('SECURITY_HEADERS', {})
        for header, value in security_headers.items():
            response.headers[header] = value
        return response
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Simple health check endpoint for monitoring"""
        return {'status': 'healthy'}, 200
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.employee import employee_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(employee_bp)
    
    # Root route - redirect to login
    @app.route('/')
    def index():
        from flask_login import current_user
        from flask import redirect, url_for
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('employee.dashboard'))
        return redirect(url_for('auth.login'))
    
    # Temporary dev login (REMOVE IN PRODUCTION)
    @app.route('/dev-login/<emp_code>')
    def dev_login(emp_code):
        """Development login bypass - FOR TESTING ONLY"""
        from flask import flash, redirect, url_for
        from flask_login import login_user
        from app.models import Employee
        
        if not app.debug:
            flash('Dev login is only available in debug mode', 'error')
            return redirect(url_for('auth.login'))
        
        employee = Employee.query.filter_by(emp_code=emp_code).first()
        
        if not employee:
            flash(f'Employee with code {emp_code} not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Log in the employee directly
        login_user(employee)
        flash(f'Logged in as {employee.name} (Dev Mode)', 'success')
        
        if employee.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))
    
    return app
