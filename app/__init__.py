import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import RequestEntityTooLarge
from config import config
from app.models import db, bcrypt

login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_name='default'):
    """Flask application factory."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
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
    csrf.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login with error handling."""
        from app.models import User
        try:
            user_id_int = int(user_id)
            return User.query.get(user_id_int)
        except (ValueError, TypeError):
            return None
    
    # Register error handler for file upload size limit
    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(e):
        return 'File is too large. Maximum size is 10MB.', 413
    
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
    
    return app
