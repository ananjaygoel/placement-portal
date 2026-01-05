from flask import Blueprint

bp = Blueprint("auth", __name__)


@bp.get("/login")
def login():
    # Placeholder page; full auth comes in Milestone-PPA Auth_RBAC
    return "Login (coming soon)"

