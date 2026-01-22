from __future__ import annotations

from pathlib import Path

from flask import Blueprint, abort, current_app, send_file
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Application, Drive, Student

bp = Blueprint("files", __name__)


@bp.get("/resumes/<int:student_id>")
@login_required
def student_resume(student_id: int):
    student = Student.query.get_or_404(student_id)
    if not student.resume_path:
        abort(404)

    # Access control:
    # - Admin: can view any resume
    # - Company: can view resumes of students who applied to its drives
    # - Student: can view only their own resume
    if current_user.role == "admin":
        allowed = True
    elif current_user.role == "company":
        allowed = (
            db.session.query(Application.id)
            .join(Drive, Application.drive_id == Drive.id)
            .filter(Application.student_id == student.user_id, Drive.company_id == current_user.id)
            .first()
            is not None
        )
    elif current_user.role == "student":
        allowed = current_user.id == student.user_id
    else:
        allowed = False

    if not allowed:
        abort(403)

    abs_path = Path(current_app.instance_path) / student.resume_path
    if not abs_path.exists():
        abort(404)

    # Serve as attachment to avoid browser content sniffing issues.
    return send_file(
        abs_path,
        as_attachment=True,
        download_name=f"{student.student_uid}_resume.pdf",
    )

