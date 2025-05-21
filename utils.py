from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(role):
    """
    Decorator for views that require specific role access.
    Roles are hierarchical: admin > officer > analyst
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized
            
            if role == 'admin' and not current_user.is_admin():
                abort(403)  # Forbidden
            elif role == 'officer' and not current_user.is_officer():
                abort(403)
            elif role == 'analyst' and not current_user.is_analyst():
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator