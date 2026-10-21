from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user
from app.forms import LoginForm
from app.models import User
from app import limiter
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("30 per minute")  # Rate limit: 30 login attempts per minute
def login():
    """Login route for user authentication."""
    if current_user.is_authenticated:
        # Redirect to role-based dashboard
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        try:
            username = form.username.data
            password = form.password.data
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                if not user.is_active:
                    flash('Account is inactive. Contact administrator.', 'error')
                    logger.warning(f"Inactive user login attempt: {username}")
                    return render_template('login.html', form=form)
                
                login_user(user)
                logger.info(f"User logged in: {username}")
                
                # Redirect to role-based dashboard
                if user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                else:
                    return redirect(url_for('employee.dashboard'))
            else:
                flash('Invalid username or password', 'error')
                logger.warning(f"Failed login attempt for username: {username}")
        except Exception as e:
            logger.error(f"Error during login: {str(e)}", exc_info=True)
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    """Logout route."""
    logout_user()
    return redirect(url_for('auth.login'))
