from functools import wraps
from flask import abort, flash
from flask_login import current_user

def role_required(role):
    """
    Decorator to restrict access based on user role.
    Usage: @role_required('admin') or @role_required('officer')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(403)
            
            if role == 'admin' and not current_user.is_admin():
                flash('You do not have permission to access this page.', 'danger')
                return abort(403)
            
            if role == 'officer' and not current_user.is_officer():
                flash('You do not have permission to access this page.', 'danger')
                return abort(403)
            
            if role == 'analyst' and not current_user.is_analyst():
                flash('You do not have permission to access this page.', 'danger')
                return abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
