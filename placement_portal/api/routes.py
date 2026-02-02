from __future__ import annotations

from datetime import date, datetime

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_user, logout_user
from sqlalchemy import or_
from werkzeug.exceptions import HTTPException

from ..decorators import roles_required
from ..extensions import csrf, db
from ..models import Application, Company, Drive, Notification, Placement, Student, User
from .serializers import (
    application_to_dict,
    company_to_dict,
    drive_to_dict,
    notification_to_dict,
    student_to_dict,
    user_to_dict,
)


bp = Blueprint("api", __name__)
csrf.exempt(bp)


@bp.errorhandler(HTTPException)
def _http_error(err: HTTPException):
    return (
        jsonify({"success": False, "error": err.name, "description": err.description}),
        err.code,
    )


def _json():
    return request.get_json(silent=True) or {}


def _ok(data=None, status: int = 200):
    payload = {"success": True}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


def _require_company_ok(company: Company | None) -> None:
    if company is None:
        abort(403, description="Company profile missing.")
    if not current_user.is_active:
        abort(403, description="Account is deactivated.")
    if company.is_blacklisted:
        abort(403, description="Company is blacklisted.")
    if company.approval_status != "approved":
        abort(403, description="Company is not approved.")


@bp.get("/health")
def health():
    return _ok({"status": "ok", "server_time": datetime.utcnow().isoformat()})


# --- Session / Auth (JSON) ---


@bp.post("/session")
def create_session():
    data = _json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        abort(400, description="email and password are required.")

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        abort(401, description="Invalid email or password.")

    if not user.is_active:
        abort(403, description="Account is deactivated.")

    if user.role == "company":
        _require_company_ok(user.company_profile)

    if user.role == "student":
        student = user.student_profile
        if student is None:
            abort(403, description="Student profile missing.")
        if student.is_blacklisted:
            abort(403, description="Student is blacklisted.")

    login_user(user)
    return _ok({"user": user_to_dict(user)}, status=200)


@bp.delete("/session")
@roles_required("admin", "company", "student")
def delete_session():
    logout_user()
    return _ok({"message": "logged_out"})


@bp.get("/me")
@roles_required("admin", "company", "student")
def me():
    return _ok({"user": user_to_dict(current_user)})


# --- Students ---


@bp.get("/students")
@roles_required("admin")
def list_students():
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
    return _ok({"students": [student_to_dict(s) for s in items]})


@bp.get("/students/<int:student_id>")
@roles_required("admin", "student")
def get_student(student_id: int):
    student = Student.query.get_or_404(student_id)
    if current_user.role == "student" and current_user.id != student.user_id:
        abort(403, description="Not allowed.")
    data = student_to_dict(student)
    data["email"] = student.user.email
    data["is_active"] = bool(student.user.is_active)
    return _ok({"student": data})


@bp.route("/students/<int:student_id>", methods=["PATCH", "PUT"])
@roles_required("admin", "student")
def update_student(student_id: int):
    student = Student.query.get_or_404(student_id)
    if current_user.role == "student" and current_user.id != student.user_id:
        abort(403, description="Not allowed.")

    data = _json()

    # Common editable fields
    for key in ["degree", "department", "phone", "skills"]:
        if key in data:
            setattr(student, key, (data.get(key) or "").strip() or None)

    if "full_name" in data:
        name = (data.get("full_name") or "").strip()
        if not name:
            abort(400, description="full_name cannot be empty.")
        student.full_name = name

    if "graduation_year" in data:
        student.graduation_year = data.get("graduation_year")
    if "cgpa" in data:
        student.cgpa = data.get("cgpa")

    if current_user.role == "admin":
        if "is_blacklisted" in data:
            student.is_blacklisted = bool(data.get("is_blacklisted"))
        if "is_active" in data:
            student.user.is_active = bool(data.get("is_active"))

    db.session.commit()
    return _ok({"student": student_to_dict(student)})


@bp.delete("/students/<int:student_id>")
@roles_required("admin")
def deactivate_student(student_id: int):
    user = User.query.get_or_404(student_id)
    if user.role != "student":
        abort(400, description="Not a student account.")
    user.is_active = False
    db.session.commit()
    return _ok({"message": "student_deactivated", "user": user_to_dict(user)})


# --- Companies ---


@bp.get("/companies")
@roles_required("admin")
def list_companies():
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
    return _ok({"companies": [company_to_dict(c) for c in items]})


@bp.get("/companies/<int:company_id>")
@roles_required("admin", "company")
def get_company(company_id: int):
    company = Company.query.get_or_404(company_id)
    if current_user.role == "company" and current_user.id != company.user_id:
        abort(403, description="Not allowed.")
    data = company_to_dict(company)
    data["email"] = company.user.email
    data["is_active"] = bool(company.user.is_active)
    return _ok({"company": data})


@bp.route("/companies/<int:company_id>", methods=["PATCH", "PUT"])
@roles_required("admin", "company")
def update_company(company_id: int):
    company = Company.query.get_or_404(company_id)
    if current_user.role == "company" and current_user.id != company.user_id:
        abort(403, description="Not allowed.")

    data = _json()

    editable = ["company_name", "industry", "hr_name", "hr_email", "hr_phone", "website", "description"]
    for key in editable:
        if key in data:
            val = (data.get(key) or "").strip()
            if key == "hr_email":
                val = val.lower()
            if key == "company_name" and not val:
                abort(400, description="company_name cannot be empty.")
            setattr(company, key, val or None)

    # Admin-only fields
    if current_user.role == "admin":
        if "approval_status" in data:
            status = (data.get("approval_status") or "").strip().lower()
            if status not in {"pending", "approved", "rejected"}:
                abort(400, description="Invalid approval_status.")
            company.approval_status = status
        if "is_blacklisted" in data:
            company.is_blacklisted = bool(data.get("is_blacklisted"))
        if "is_active" in data:
            company.user.is_active = bool(data.get("is_active"))

    db.session.commit()
    return _ok({"company": company_to_dict(company)})


@bp.delete("/companies/<int:company_id>")
@roles_required("admin")
def deactivate_company(company_id: int):
    user = User.query.get_or_404(company_id)
    if user.role != "company":
        abort(400, description="Not a company account.")
    user.is_active = False
    db.session.commit()
    return _ok({"message": "company_deactivated", "user": user_to_dict(user)})


# --- Drives (Job postings / placement drives) ---


@bp.get("/drives")
def list_drives():
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()

    query = Drive.query.join(Company, Drive.company_id == Company.user_id).filter(Drive.is_deleted.is_(False))

    if current_user.is_authenticated:
        if current_user.role == "admin":
            pass
        elif current_user.role == "company":
            query = query.filter(Drive.company_id == current_user.id)
        else:
            query = query.filter(
                Drive.status == "approved",
                Company.approval_status == "approved",
                Company.is_blacklisted.is_(False),
            ).filter((Drive.application_deadline.is_(None)) | (Drive.application_deadline >= date.today()))
    else:
        query = query.filter(
            Drive.status == "approved",
            Company.approval_status == "approved",
            Company.is_blacklisted.is_(False),
        ).filter((Drive.application_deadline.is_(None)) | (Drive.application_deadline >= date.today()))

    if status:
        query = query.filter(Drive.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Drive.job_title.ilike(like))
            | (Company.company_name.ilike(like))
            | (Drive.required_skills.ilike(like))
        )

    items = query.order_by(Drive.created_at.desc()).all()
    return _ok({"drives": [drive_to_dict(d) for d in items]})


@bp.post("/drives")
@roles_required("company")
def create_drive():
    company = current_user.company_profile
    _require_company_ok(company)

    data = _json()
    title = (data.get("job_title") or "").strip()
    desc = (data.get("job_description") or "").strip()

    if not title or not desc:
        abort(400, description="job_title and job_description are required.")

    deadline = data.get("application_deadline")
    deadline_dt = None
    if deadline:
        try:
            deadline_dt = date.fromisoformat(str(deadline))
        except ValueError:
            abort(400, description="application_deadline must be YYYY-MM-DD.")

    drive = Drive(
        company_id=current_user.id,
        job_title=title,
        job_description=desc,
        eligibility_criteria=(data.get("eligibility_criteria") or "").strip() or None,
        required_skills=(data.get("required_skills") or "").strip() or None,
        min_cgpa=data.get("min_cgpa"),
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
        location=(data.get("location") or "").strip() or None,
        min_experience_years=data.get("min_experience_years"),
        application_deadline=deadline_dt,
        status="pending",
    )
    db.session.add(drive)
    db.session.commit()
    return _ok({"drive": drive_to_dict(drive)}, status=201)


@bp.route("/drives/<int:drive_id>", methods=["PATCH", "PUT"])
@roles_required("admin", "company")
def update_drive(drive_id: int):
    drive = Drive.query.get_or_404(drive_id)
    data = _json()

    if current_user.role == "company":
        company = current_user.company_profile
        _require_company_ok(company)
        if drive.company_id != current_user.id:
            abort(403, description="Not allowed.")

        # Editable fields for company
        for key in ["eligibility_criteria", "required_skills", "location"]:
            if key in data:
                setattr(drive, key, (data.get(key) or "").strip() or None)

        if "job_title" in data:
            title = (data.get("job_title") or "").strip()
            if not title:
                abort(400, description="job_title cannot be empty.")
            drive.job_title = title

        if "job_description" in data:
            desc = (data.get("job_description") or "").strip()
            if not desc:
                abort(400, description="job_description cannot be empty.")
            drive.job_description = desc

        for key in ["min_cgpa", "salary_min", "salary_max", "min_experience_years"]:
            if key in data:
                setattr(drive, key, data.get(key))

        if "application_deadline" in data:
            deadline = data.get("application_deadline")
            if deadline:
                try:
                    drive.application_deadline = date.fromisoformat(str(deadline))
                except ValueError:
                    abort(400, description="application_deadline must be YYYY-MM-DD.")
            else:
                drive.application_deadline = None

        if "status" in data:
            status = (data.get("status") or "").strip().lower()
            if status not in {"closed"}:
                abort(400, description="Company can only set status=closed.")
            drive.status = status

        # Re-approval if an approved drive is edited
        if drive.status == "approved":
            drive.status = "pending"

    else:
        # Admin can approve/reject/close
        if "status" in data:
            status = (data.get("status") or "").strip().lower()
            if status not in {"pending", "approved", "rejected", "closed"}:
                abort(400, description="Invalid status.")
            drive.status = status

    db.session.commit()
    return _ok({"drive": drive_to_dict(drive)})


@bp.delete("/drives/<int:drive_id>")
@roles_required("company")
def delete_drive(drive_id: int):
    drive = Drive.query.get_or_404(drive_id)
    company = current_user.company_profile
    _require_company_ok(company)
    if drive.company_id != current_user.id:
        abort(403, description="Not allowed.")
    drive.is_deleted = True
    db.session.commit()
    return _ok({"message": "drive_deleted"})


# --- Applications ---


@bp.get("/applications")
@roles_required("admin", "company", "student")
def list_applications():
    status = (request.args.get("status") or "").strip().lower()
    drive_id = request.args.get("drive_id")
    student_id = request.args.get("student_id")

    query = Application.query.join(Drive, Application.drive_id == Drive.id).join(
        Company, Drive.company_id == Company.user_id
    )

    if current_user.role == "admin":
        pass
    elif current_user.role == "company":
        company = current_user.company_profile
        _require_company_ok(company)
        query = query.filter(Drive.company_id == current_user.id)
    else:
        query = query.filter(Application.student_id == current_user.id)

    if status:
        query = query.filter(Application.status == status)
    if drive_id and str(drive_id).isdigit():
        query = query.filter(Application.drive_id == int(drive_id))
    if student_id and str(student_id).isdigit() and current_user.role == "admin":
        query = query.filter(Application.student_id == int(student_id))

    items = query.order_by(Application.application_date.desc()).all()
    return _ok({"applications": [application_to_dict(a) for a in items]})


@bp.get("/applications/<int:application_id>")
@roles_required("admin", "company", "student")
def get_application(application_id: int):
    app = Application.query.get_or_404(application_id)
    if current_user.role == "admin":
        pass
    elif current_user.role == "company":
        company = current_user.company_profile
        _require_company_ok(company)
        if app.drive.company_id != current_user.id:
            abort(403, description="Not allowed.")
    else:
        if app.student_id != current_user.id:
            abort(403, description="Not allowed.")
    return _ok({"application": application_to_dict(app)})


@bp.post("/applications")
@roles_required("student")
def create_application():
    data = _json()
    drive_id = data.get("drive_id")
    if not drive_id or not str(drive_id).isdigit():
        abort(400, description="drive_id is required.")

    drive = Drive.query.get_or_404(int(drive_id))
    if drive.is_deleted or drive.status != "approved":
        abort(400, description="Drive is not available.")
    if drive.company.approval_status != "approved" or drive.company.is_blacklisted:
        abort(400, description="Drive is not available.")
    if drive.application_deadline and drive.application_deadline < date.today():
        abort(400, description="Application deadline has passed.")

    existing = Application.query.filter_by(student_id=current_user.id, drive_id=drive.id).first()
    if existing is not None:
        return _ok({"application": application_to_dict(existing), "message": "already_applied"}, status=200)

    app = Application(student_id=current_user.id, drive_id=drive.id, status="applied")
    db.session.add(app)
    db.session.commit()
    return _ok({"application": application_to_dict(app)}, status=201)


@bp.route("/applications/<int:application_id>", methods=["PATCH", "PUT"])
@roles_required("admin", "company")
def update_application(application_id: int):
    data = _json()
    status = (data.get("status") or "").strip().lower()
    if status not in {"shortlisted", "selected", "rejected"}:
        abort(400, description="status must be one of: shortlisted, selected, rejected.")

    app = Application.query.get_or_404(application_id)
    if current_user.role == "company":
        company = current_user.company_profile
        _require_company_ok(company)
        if app.drive.company_id != current_user.id:
            abort(403, description="Not allowed.")

    if app.status == status:
        return _ok({"application": application_to_dict(app), "message": "status_unchanged"})

    app.status = status
    db.session.add(
        Notification(
            user_id=app.student_id,
            message=(
                f"Application update: {app.drive.job_title} at {app.drive.company.company_name} is now '{status}'."
            ),
        )
    )

    if status == "selected" and app.placement is None:
        db.session.add(Placement(application_id=app.id))

    db.session.commit()
    return _ok({"application": application_to_dict(app)})


@bp.delete("/applications/<int:application_id>")
@roles_required("student")
def withdraw_application(application_id: int):
    """Allow students to withdraw only if still in 'applied' status."""
    app = Application.query.get_or_404(application_id)
    if app.student_id != current_user.id:
        abort(403, description="Not allowed.")
    if app.status != "applied":
        abort(400, description="Only applications in 'applied' status can be withdrawn.")

    db.session.delete(app)
    db.session.commit()
    return _ok({"message": "application_withdrawn"})


# --- Notifications (student) ---


@bp.get("/notifications")
@roles_required("student")
def list_notifications():
    items = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return _ok({"notifications": [notification_to_dict(n) for n in items]})


@bp.post("/notifications/<int:notification_id>/read")
@roles_required("student")
def mark_notification_read(notification_id: int):
    notif = Notification.query.get_or_404(notification_id)
    if notif.user_id != current_user.id:
        abort(403, description="Not allowed.")
    notif.is_read = True
    db.session.commit()
    return _ok({"notification": notification_to_dict(notif)})
