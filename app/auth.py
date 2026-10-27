from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not current_user.is_active:
            abort(403)
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def employee_required(f):
    """Decorator to require employee role for a route (admins also have access)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not current_user.is_active:
            abort(403)
        # Allow both employees and admins
        if current_user.role not in ['employee', 'admin']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
