from flask import Blueprint, render_template
from flask_login import login_required

from ..decorators import roles_required

bp = Blueprint("company", __name__)


@bp.get("/")
@login_required
@roles_required("company")
def dashboard():
    return render_template("company/dashboard.html")

