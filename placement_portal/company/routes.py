from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ..decorators import roles_required
from ..extensions import db
from ..models import Application, Drive
from .forms import DriveForm

bp = Blueprint("company", __name__)


@bp.get("/")
@login_required
@roles_required("company")
def dashboard():
    drives = (
        Drive.query.filter_by(company_id=current_user.id, is_deleted=False)
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

    return render_template("company/dashboard.html", drives=drives, applicant_counts=counts)


@bp.route("/drives/new", methods=["GET", "POST"])
@login_required
@roles_required("company")
def create_drive():
    form = DriveForm()
    if form.validate_on_submit():
        drive = Drive(
            company_id=current_user.id,
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
    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id or drive.is_deleted:
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
    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id or drive.is_deleted:
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
    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id or drive.is_deleted:
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
    drive = Drive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id or drive.is_deleted:
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
    app = Application.query.get_or_404(application_id)
    if app.drive.company_id != current_user.id:
        flash("Not allowed.", "danger")
        return redirect(url_for("company.dashboard"))

    status = (request.form.get("status") or "").strip().lower()
    if status not in {"shortlisted", "selected", "rejected"}:
        flash("Invalid status.", "danger")
        return redirect(url_for("company.drive_applications", drive_id=app.drive_id))

    app.status = status
    db.session.commit()
    flash("Application status updated.", "success")
    return redirect(url_for("company.drive_applications", drive_id=app.drive_id))
