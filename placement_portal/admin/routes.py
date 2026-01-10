from flask import Blueprint, render_template
from flask_login import login_required

from ..decorators import roles_required

bp = Blueprint("admin", __name__)


@bp.get("/")
@login_required
@roles_required("admin")
def dashboard():
    return render_template("admin/dashboard.html")

