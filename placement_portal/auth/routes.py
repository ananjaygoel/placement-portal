from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import Company, Student, User
from .forms import CompanyRegistrationForm, LoginForm, StudentRegistrationForm

bp = Blueprint("auth", __name__)


def _dashboard_url_for(user: User) -> str:
    if user.role == "admin":
        return url_for("admin.dashboard")
    if user.role == "company":
        return url_for("company.dashboard")
    if user.role == "student":
        return url_for("student.dashboard")
    return url_for("main.index")


def _save_resume(file_storage) -> str:
    """Save a resume under instance/uploads/resumes and return the relative path."""
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


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_dashboard_url_for(current_user))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if not user.is_active:
            flash("Your account is deactivated. Contact the placement cell.", "danger")
            return redirect(url_for("auth.login"))

        if user.role == "company":
            company = user.company_profile
            if company is None:
                flash("Company profile missing. Contact the placement cell.", "danger")
                return redirect(url_for("auth.login"))
            if company.is_blacklisted:
                flash("Company account is blacklisted.", "danger")
                return redirect(url_for("auth.login"))
            if company.approval_status != "approved":
                flash("Company login is enabled only after admin approval.", "warning")
                return redirect(url_for("auth.login"))

        if user.role == "student":
            student = user.student_profile
            if student is None:
                flash("Student profile missing. Contact the placement cell.", "danger")
                return redirect(url_for("auth.login"))
            if student.is_blacklisted:
                flash("Student account is blacklisted.", "danger")
                return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(_dashboard_url_for(user))

    return render_template("auth/login.html", form=form)


@bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.index"))


@bp.route("/register/student", methods=["GET", "POST"])
def register_student():
    if current_user.is_authenticated:
        return redirect(_dashboard_url_for(current_user))

    form = StudentRegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first() is not None:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("auth.login"))

        if Student.query.filter_by(student_uid=form.student_uid.data.strip()).first() is not None:
            flash("Student ID already registered.", "warning")
            return redirect(url_for("auth.register_student"))

        user = User(email=email, role="student")
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # assign user.id without committing

        resume_rel_path = None
        if form.resume.data:
            try:
                resume_rel_path = _save_resume(form.resume.data)
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("auth.register_student"))

        student = Student(
            user_id=user.id,
            student_uid=form.student_uid.data.strip(),
            full_name=form.full_name.data.strip(),
            degree=(form.degree.data or "").strip() or None,
            department=(form.department.data or "").strip() or None,
            graduation_year=form.graduation_year.data,
            cgpa=float(form.cgpa.data) if form.cgpa.data is not None else None,
            phone=(form.phone.data or "").strip() or None,
            skills=(form.skills.data or "").strip() or None,
            resume_path=resume_rel_path,
        )
        db.session.add(student)
        db.session.commit()

        login_user(user)
        flash("Student account created.", "success")
        return redirect(_dashboard_url_for(user))

    return render_template("auth/register_student.html", form=form)


@bp.route("/register/company", methods=["GET", "POST"])
def register_company():
    if current_user.is_authenticated:
        return redirect(_dashboard_url_for(current_user))

    form = CompanyRegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first() is not None:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("auth.login"))

        user = User(email=email, role="company")
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        company = Company(
            user_id=user.id,
            company_name=form.company_name.data.strip(),
            industry=(form.industry.data or "").strip() or "Other",
            hr_name=(form.hr_name.data or "").strip() or None,
            hr_email=(form.hr_email.data or "").strip().lower() or None,
            hr_phone=(form.hr_phone.data or "").strip() or None,
            website=(form.website.data or "").strip() or None,
            description=(form.description.data or "").strip() or None,
            approval_status="pending",
        )
        db.session.add(company)
        db.session.commit()

        flash("Company registered. You can login only after admin approval.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_company.html", form=form)
