from functools import wraps
from flask_login import current_user
from flask import redirect, url_for

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        if not current_user.is_admin:
            return redirect(url_for("pages.dashboard"))

        return func(*args, **kwargs)
    return wrapper
