from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from werkzeug.utils import secure_filename

from ..decorators import roles_required
from ..extensions import db
from ..models import Application, Company, Drive, Notification, Placement, Student
from .forms import StudentProfileForm

bp = Blueprint("student", __name__)


@bp.get("/")
@login_required
@roles_required("student")
def dashboard():
    q = (request.args.get("q") or "").strip()

    drives_query = (
        Drive.query.join(Company, Drive.company_id == Company.user_id)
        .filter(
            Drive.status == "approved",
            Drive.is_deleted.is_(False),
            Company.approval_status == "approved",
            Company.is_blacklisted.is_(False),
        )
        .filter((Drive.application_deadline.is_(None)) | (Drive.application_deadline >= date.today()))
    )

    if q:
        like = f"%{q}%"
        drives_query = drives_query.filter(
            (Drive.job_title.ilike(like))
            | (Company.company_name.ilike(like))
            | (Drive.required_skills.ilike(like))
        )

    drives = drives_query.order_by(Drive.created_at.desc()).all()

    applications = (
        Application.query.filter_by(student_id=current_user.id)
        .order_by(Application.application_date.desc())
        .all()
    )
    applied_drive_ids = {a.drive_id for a in applications}

    status_rows = (
        db.session.query(Application.status, func.count(Application.id))
        .filter(Application.student_id == current_user.id)
        .group_by(Application.status)
        .all()
    )
    status_map = {status: int(count) for status, count in status_rows}
    status_labels = ["applied", "shortlisted", "selected", "rejected"]
    status_values = [status_map.get(label, 0) for label in status_labels]

    placements = (
        Placement.query.join(Application, Placement.application_id == Application.id)
        .filter(Application.student_id == current_user.id)
        .order_by(Placement.placed_on.desc())
        .all()
    )

    notifications = (
        Notification.query.filter_by(user_id=current_user.id, is_read=False)
        .order_by(Notification.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "student/dashboard.html",
        q=q,
        drives=drives,
        applications=applications,
        applied_drive_ids=applied_drive_ids,
        placements=placements,
        notifications=notifications,
        status_labels=status_labels,
        status_values=status_values,
        today=date.today(),
    )


@bp.get("/drives/<int:drive_id>")
@login_required
@roles_required("student")
def drive_detail(drive_id: int):
    drive = Drive.query.get_or_404(drive_id)
    if drive.is_deleted or drive.status != "approved":
        abort(404)
    if drive.company.approval_status != "approved" or drive.company.is_blacklisted:
        abort(404)
    if drive.application_deadline and drive.application_deadline < date.today():
        abort(404)

    existing = Application.query.filter_by(student_id=current_user.id, drive_id=drive.id).first()
    return render_template("student/drive_detail.html", drive=drive, existing=existing)


@bp.post("/drives/<int:drive_id>/apply")
@login_required
@roles_required("student")
def apply(drive_id: int):
    drive = Drive.query.get_or_404(drive_id)
    if drive.is_deleted or drive.status != "approved":
        flash("This drive is not available.", "warning")
        return redirect(url_for("student.dashboard"))
    if drive.company.approval_status != "approved" or drive.company.is_blacklisted:
        flash("This drive is not available.", "warning")
        return redirect(url_for("student.dashboard"))
    if drive.application_deadline and drive.application_deadline < date.today():
        flash("Application deadline has passed.", "warning")
        return redirect(url_for("student.dashboard"))

    existing = Application.query.filter_by(student_id=current_user.id, drive_id=drive.id).first()
    if existing is not None:
        flash("You have already applied to this drive.", "info")
        return redirect(url_for("student.drive_detail", drive_id=drive.id))

    db.session.add(Application(student_id=current_user.id, drive_id=drive.id, status="applied"))
    db.session.commit()
    flash("Application submitted.", "success")
    return redirect(url_for("student.dashboard"))


def _save_resume(file_storage) -> str:
    filename = secure_filename(file_storage.filename or "")
    ext = Path(filename).suffix.lower()
    if ext != ".pdf":
        raise ValueError("Only PDF resumes are allowed.")

    dest_dir = Path(current_app.instance_path) / "uploads" / "resumes"
    dest_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}.pdf"
    dest_path = dest_dir / stored_name
    file_storage.save(dest_path)
    return str(Path("uploads") / "resumes" / stored_name)


@bp.route("/profile", methods=["GET", "POST"])
@login_required
@roles_required("student")
def profile():
    student = Student.query.get_or_404(current_user.id)
    form = StudentProfileForm(obj=student)

    if form.validate_on_submit():
        student.full_name = form.full_name.data.strip()
        student.degree = (form.degree.data or "").strip() or None
        student.department = (form.department.data or "").strip() or None
        student.graduation_year = form.graduation_year.data
        student.cgpa = float(form.cgpa.data) if form.cgpa.data is not None else None
        student.phone = (form.phone.data or "").strip() or None
        student.skills = (form.skills.data or "").strip() or None

        if form.resume.data:
            try:
                student.resume_path = _save_resume(form.resume.data)
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("student.profile"))

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/profile.html", form=form, student=student)


@bp.post("/notifications/<int:notification_id>/read")
@login_required
@roles_required("student")
def mark_notification_read(notification_id: int):
    notif = Notification.query.get_or_404(notification_id)
    if notif.user_id != current_user.id:
        abort(403)
    notif.is_read = True
    db.session.commit()
    flash("Notification marked as read.", "info")
    return redirect(url_for("student.dashboard"))
