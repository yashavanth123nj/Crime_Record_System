from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(role):
    """
    Decorator for views that require specific role access.
    Roles are hierarchical: admin > officer > analyst
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Admin can access everything
            if current_user.role == 'admin':
                return f(*args, **kwargs)
            
            # Officer can access officer and analyst pages
            if role == 'officer' and current_user.role != 'officer':
                flash('You need officer privileges to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            
            # Analyst can only access analyst pages
            if role == 'analyst' and current_user.role != 'analyst':
                flash('You need analyst privileges to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator