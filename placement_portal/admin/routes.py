from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from ..decorators import roles_required
from ..extensions import db
from ..models import Application, Company, Drive, Placement, Student, User

bp = Blueprint("admin", __name__)


@bp.get("/")
@login_required
@roles_required("admin")
def dashboard():
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = Drive.query.filter_by(is_deleted=False).count()
    total_applications = Application.query.count()
    total_placements = Placement.query.count()

    pending_companies = Company.query.filter_by(approval_status="pending").count()
    pending_drives = Drive.query.filter_by(status="pending", is_deleted=False).count()

    admin_overview = {
        "labels": ["Drives", "Applications", "Placements"],
        "values": [total_drives, total_applications, total_placements],
    }

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications,
        total_placements=total_placements,
        pending_companies=pending_companies,
        pending_drives=pending_drives,
        admin_overview=admin_overview,
    )


@bp.get("/companies")
@login_required
@roles_required("admin")
def companies():
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()

    query = Company.query.join(User, Company.user_id == User.id)
    if status:
        query = query.filter(Company.approval_status == status)
    if q:
        like = f"%{q}%"
        filters = [
            Company.company_name.ilike(like),
            Company.industry.ilike(like),
            User.email.ilike(like),
        ]
        if q.isdigit():
            filters.append(Company.user_id == int(q))
        query = query.filter(or_(*filters))

    items = query.order_by(Company.created_at.desc()).all()
    return render_template("admin/companies.html", companies=items, q=q, status=status)


@bp.post("/companies/<int:company_id>/approve")
@login_required
@roles_required("admin")
def approve_company(company_id: int):
    company = Company.query.get_or_404(company_id)
    company.approval_status = "approved"
    db.session.commit()
    flash("Company approved.", "success")
    return redirect(url_for("admin.companies"))


@bp.post("/companies/<int:company_id>/reject")
@login_required
@roles_required("admin")
def reject_company(company_id: int):
    company = Company.query.get_or_404(company_id)
    company.approval_status = "rejected"
    db.session.commit()
    flash("Company rejected.", "warning")
    return redirect(url_for("admin.companies"))


@bp.post("/companies/<int:company_id>/toggle-blacklist")
@login_required
@roles_required("admin")
def toggle_company_blacklist(company_id: int):
    company = Company.query.get_or_404(company_id)
    company.is_blacklisted = not company.is_blacklisted
    db.session.commit()
    flash("Company blacklist updated.", "info")
    return redirect(url_for("admin.companies"))


@bp.post("/companies/<int:company_id>/toggle-active")
@login_required
@roles_required("admin")
def toggle_company_active(company_id: int):
    user = User.query.get_or_404(company_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash("Company account active status updated.", "info")
    return redirect(url_for("admin.companies"))


@bp.get("/students")
@login_required
@roles_required("admin")
def students():
    q = (request.args.get("q") or "").strip()

    query = Student.query.join(User, Student.user_id == User.id)
    if q:
        like = f"%{q}%"
        filters = [
            Student.full_name.ilike(like),
            Student.student_uid.ilike(like),
            Student.phone.ilike(like),
            User.email.ilike(like),
        ]
        if q.isdigit():
            filters.append(Student.user_id == int(q))
        query = query.filter(or_(*filters))

    items = query.order_by(Student.created_at.desc()).all()
    return render_template("admin/students.html", students=items, q=q)


@bp.post("/students/<int:student_id>/toggle-blacklist")
@login_required
@roles_required("admin")
def toggle_student_blacklist(student_id: int):
    student = Student.query.get_or_404(student_id)
    student.is_blacklisted = not student.is_blacklisted
    db.session.commit()
    flash("Student blacklist updated.", "info")
    return redirect(url_for("admin.students"))


@bp.post("/students/<int:student_id>/toggle-active")
@login_required
@roles_required("admin")
def toggle_student_active(student_id: int):
    user = User.query.get_or_404(student_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash("Student account active status updated.", "info")
    return redirect(url_for("admin.students"))


@bp.get("/drives")
@login_required
@roles_required("admin")
def drives():
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()

    query = Drive.query.join(Company, Drive.company_id == Company.user_id)
    if status:
        query = query.filter(Drive.status == status)
    query = query.filter(Drive.is_deleted.is_(False))

    if q:
        like = f"%{q}%"
        filters = [
            Drive.job_title.ilike(like),
            Company.company_name.ilike(like),
        ]
        if q.isdigit():
            filters.append(Drive.id == int(q))
        query = query.filter(or_(*filters))

    items = query.order_by(Drive.created_at.desc()).all()
    return render_template("admin/drives.html", drives=items, q=q, status=status)


@bp.post("/drives/<int:drive_id>/approve")
@login_required
@roles_required("admin")
def approve_drive(drive_id: int):
    drive = Drive.query.get_or_404(drive_id)
    drive.status = "approved"
    db.session.commit()
    flash("Drive approved.", "success")
    return redirect(url_for("admin.drives"))


@bp.post("/drives/<int:drive_id>/reject")
@login_required
@roles_required("admin")
def reject_drive(drive_id: int):
    drive = Drive.query.get_or_404(drive_id)
    drive.status = "rejected"
    db.session.commit()
    flash("Drive rejected.", "warning")
    return redirect(url_for("admin.drives"))


@bp.get("/applications")
@login_required
@roles_required("admin")
def applications():
    q = (request.args.get("q") or "").strip()

    query = (
        Application.query.join(Student, Application.student_id == Student.user_id)
        .join(User, Student.user_id == User.id)
        .join(Drive, Application.drive_id == Drive.id)
        .join(Company, Drive.company_id == Company.user_id)
    )

    if q:
        like = f"%{q}%"
        filters = [
            User.email.ilike(like),
            Student.full_name.ilike(like),
            Student.student_uid.ilike(like),
            Drive.job_title.ilike(like),
            Company.company_name.ilike(like),
        ]
        if q.isdigit():
            filters.append(Application.id == int(q))
        query = query.filter(or_(*filters))

    items = query.order_by(Application.application_date.desc()).all()
    return render_template("admin/applications.html", applications=items, q=q)


@bp.get("/placements")
@login_required
@roles_required("admin")
def placements():
    q = (request.args.get("q") or "").strip()

    query = (
        Placement.query.join(Application, Placement.application_id == Application.id)
        .join(Student, Application.student_id == Student.user_id)
        .join(User, Student.user_id == User.id)
        .join(Drive, Application.drive_id == Drive.id)
        .join(Company, Drive.company_id == Company.user_id)
    )

    if q:
        like = f"%{q}%"
        filters = [
            User.email.ilike(like),
            Student.full_name.ilike(like),
            Student.student_uid.ilike(like),
            Company.company_name.ilike(like),
            Drive.job_title.ilike(like),
        ]
        if q.isdigit():
            filters.append(Placement.id == int(q))
        query = query.filter(or_(*filters))

    items = query.order_by(Placement.placed_on.desc()).all()
    return render_template("admin/placements.html", placements=items, q=q)
