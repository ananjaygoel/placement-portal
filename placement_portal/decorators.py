from __future__ import annotations

from functools import wraps

from flask import abort
from flask_login import current_user


def roles_required(*roles: str):
    """Restrict a route to authenticated users whose role is in `roles`."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator

