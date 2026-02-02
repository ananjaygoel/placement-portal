from __future__ import annotations

from datetime import date, datetime, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user
from sqlalchemy import func

from ..decorators import roles_required
from ..extensions import db
from ..models import Application, Drive, Notification, Placement
from .forms import DriveForm

bp = Blueprint("company", __name__)

@bp.before_request
def _company_guard():
    # If a company gets deactivated/blacklisted after login, invalidate the session.
    if not current_user.is_authenticated:
        return None
    if current_user.role != "company":
        abort(403)

    company = current_user.company_profile
    if (
        company is None
        or not current_user.is_active
        or company.is_blacklisted
        or company.approval_status != "approved"
    ):
        logout_user()
        flash("Company access revoked. Contact the placement cell.", "danger")
        return redirect(url_for("auth.login"))


@bp.get("/")
@login_required
@roles_required("company")
def dashboard():
    company = current_user.company_profile

    drives = (
        Drive.query.filter_by(company_id=company.user_id, is_deleted=False)
        .order_by(Drive.created_at.desc())
        .all()
    )

    drive_ids = [d.id for d in drives]
    counts = {}
    if drive_ids:
        rows = (
            db.session.query(Application.drive_id, func.count(Application.id))
            .filter(Application.drive_id.in_(drive_ids))
            .group_by(Application.drive_id)
            .all()
        )
        counts = {drive_id: count for drive_id, count in rows}

    # Trend: applications per day (last 30 days) across all drives of this company.
    start_day = date.today() - timedelta(days=29)
    start_dt = datetime.combine(start_day, datetime.min.time())

    trend_rows = (
        db.session.query(func.date(Application.application_date), func.count(Application.id))
        .join(Drive, Application.drive_id == Drive.id)
        .filter(Drive.company_id == company.user_id, Application.application_date >= start_dt)
        .group_by(func.date(Application.application_date))
        .all()
    )
    trend_map = {day: count for day, count in trend_rows}
    trend_labels = [(start_day + timedelta(days=i)).isoformat() for i in range(30)]
    trend_values = [int(trend_map.get(label, 0)) for label in trend_labels]

    return render_template(
        "company/dashboard.html",
        drives=drives,
        applicant_counts=counts,
        trend_labels=trend_labels,
        trend_values=trend_values,
    )


@bp.route("/drives/new", methods=["GET", "POST"])
@login_required
@roles_required("company")
def create_drive():
    company = current_user.company_profile

    form = DriveForm()
    if form.validate_on_submit():
        drive = Drive(
            company_id=company.user_id,
            job_title=form.job_title.data.strip(),
            job_description=form.job_description.data.strip(),
            eligibility_criteria=(form.eligibility_criteria.data or "").strip() or None,
            required_skills=(form.required_skills.data or "").strip() or None,
            min_cgpa=float(form.min_cgpa.data) if form.min_cgpa.data is not None else None,
            salary_min=form.salary_min.data,
            salary_max=form.salary_max.data,
            location=(form.location.data or "").strip() or None,
            min_experience_years=form.min_experience_years.data,
            application_deadline=form.application_deadline.data,
            status="pending",
        )
        db.session.add(drive)
        db.session.commit()
        flash("Drive created and sent for admin approval.", "success")
        return redirect(url_for("company.dashboard"))

    return render_template("company/drive_form.html", form=form, mode="create")


@bp.route("/drives/<int:drive_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("company")
def edit_drive(drive_id: int):
    company = current_user.company_profile

    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != company.user_id or drive.is_deleted:
        flash("Not allowed.", "danger")
        return redirect(url_for("company.dashboard"))

    form = DriveForm(obj=drive)
    if form.validate_on_submit():
        drive.job_title = form.job_title.data.strip()
        drive.job_description = form.job_description.data.strip()
        drive.eligibility_criteria = (form.eligibility_criteria.data or "").strip() or None
        drive.required_skills = (form.required_skills.data or "").strip() or None
        drive.min_cgpa = float(form.min_cgpa.data) if form.min_cgpa.data is not None else None
        drive.salary_min = form.salary_min.data
        drive.salary_max = form.salary_max.data
        drive.location = (form.location.data or "").strip() or None
        drive.min_experience_years = form.min_experience_years.data
        drive.application_deadline = form.application_deadline.data

        # If an already-approved drive is edited, it should go back for re-approval.
        if drive.status == "approved":
            drive.status = "pending"

        db.session.commit()
        flash("Drive updated.", "success")
        return redirect(url_for("company.dashboard"))

    return render_template("company/drive_form.html", form=form, mode="edit", drive=drive)


@bp.post("/drives/<int:drive_id>/close")
@login_required
@roles_required("company")
def close_drive(drive_id: int):
    company = current_user.company_profile

    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != company.user_id or drive.is_deleted:
        flash("Not allowed.", "danger")
        return redirect(url_for("company.dashboard"))

    drive.status = "closed"
    db.session.commit()
    flash("Drive closed.", "info")
    return redirect(url_for("company.dashboard"))


@bp.post("/drives/<int:drive_id>/delete")
@login_required
@roles_required("company")
def delete_drive(drive_id: int):
    company = current_user.company_profile

    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != company.user_id or drive.is_deleted:
        flash("Not allowed.", "danger")
        return redirect(url_for("company.dashboard"))

    drive.is_deleted = True
    db.session.commit()
    flash("Drive removed.", "info")
    return redirect(url_for("company.dashboard"))


@bp.get("/drives/<int:drive_id>/applications")
@login_required
@roles_required("company")
def drive_applications(drive_id: int):
    company = current_user.company_profile

    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != company.user_id or drive.is_deleted:
        flash("Not allowed.", "danger")
        return redirect(url_for("company.dashboard"))

    applications = (
        Application.query.filter_by(drive_id=drive.id)
        .order_by(Application.application_date.desc())
        .all()
    )
    return render_template(
        "company/drive_applications.html", drive=drive, applications=applications
    )


@bp.post("/applications/<int:application_id>/set-status")
@login_required
@roles_required("company")
def set_application_status(application_id: int):
    company = current_user.company_profile

    app = Application.query.get_or_404(application_id)
    if app.drive.company_id != company.user_id:
        flash("Not allowed.", "danger")
        return redirect(url_for("company.dashboard"))

    status = (request.form.get("status") or "").strip().lower()
    if status not in {"shortlisted", "selected", "rejected"}:
        flash("Invalid status.", "danger")
        return redirect(url_for("company.drive_applications", drive_id=app.drive_id))

    if app.status == status:
        flash("Status is already set.", "info")
        return redirect(url_for("company.drive_applications", drive_id=app.drive_id))

    app.status = status

    msg = (
        f"Application update: {app.drive.job_title} at {app.drive.company.company_name} is now '{status}'."
    )
    db.session.add(Notification(user_id=app.student_id, message=msg))

    if status == "selected" and app.placement is None:
        # Create a placement record for history tracking (offer details can be extended later).
        db.session.add(Placement(application_id=app.id))
    db.session.commit()
    flash("Application status updated.", "success")
    return redirect(url_for("company.drive_applications", drive_id=app.drive_id))
