from __future__ import annotations

from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # "admin" | "company" | "student"
    role = db.Column(db.String(20), nullable=False, index=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    admin_profile = db.relationship("Admin", back_populates="user", uselist=False)
    company_profile = db.relationship("Company", back_populates="user", uselist=False)
    student_profile = db.relationship("Student", back_populates="user", uselist=False)

    def set_password(self, password: str) -> None:
        # Werkzeug >=3 defaults to scrypt, but some Python builds (notably the
        # system Python on certain macOS setups) may not have hashlib.scrypt.
        # PBKDF2 is widely supported and sufficient for this course project.
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Admin(db.Model):
    __tablename__ = "admins"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="admin_profile")


class Company(db.Model):
    __tablename__ = "companies"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)

    company_name = db.Column(db.String(200), nullable=False, index=True)
    industry = db.Column(db.String(120), nullable=False, default="Other", index=True)

    hr_name = db.Column(db.String(120), nullable=True)
    hr_email = db.Column(db.String(255), nullable=True)
    hr_phone = db.Column(db.String(30), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)

    approval_status = db.Column(
        db.String(20), nullable=False, default="pending", index=True
    )  # pending/approved/rejected
    is_blacklisted = db.Column(db.Boolean, nullable=False, default=False, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", back_populates="company_profile")
    drives = db.relationship("Drive", back_populates="company")


class Student(db.Model):
    __tablename__ = "students"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)

    student_uid = db.Column(db.String(50), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(200), nullable=False, index=True)
    degree = db.Column(db.String(120), nullable=True)
    department = db.Column(db.String(120), nullable=True, index=True)
    graduation_year = db.Column(db.Integer, nullable=True, index=True)
    cgpa = db.Column(db.Float, nullable=True, index=True)
    phone = db.Column(db.String(30), nullable=True, index=True)

    skills = db.Column(db.Text, nullable=True)
    resume_path = db.Column(db.String(500), nullable=True)

    is_blacklisted = db.Column(db.Boolean, nullable=False, default=False, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", back_populates="student_profile")
    applications = db.relationship("Application", back_populates="student")


class Drive(db.Model):
    __tablename__ = "drives"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.user_id"), nullable=False, index=True
    )

    job_title = db.Column(db.String(200), nullable=False, index=True)
    job_description = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.Text, nullable=True)
    required_skills = db.Column(db.Text, nullable=True)

    min_cgpa = db.Column(db.Float, nullable=True)
    salary_min = db.Column(db.Integer, nullable=True)
    salary_max = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    min_experience_years = db.Column(db.Integer, nullable=True)

    application_deadline = db.Column(db.Date, nullable=True, index=True)

    status = db.Column(
        db.String(20), nullable=False, default="pending", index=True
    )  # pending/approved/rejected/closed
    is_deleted = db.Column(db.Boolean, nullable=False, default=False, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    company = db.relationship("Company", back_populates="drives")
    applications = db.relationship("Application", back_populates="drive")


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.user_id"), nullable=False, index=True
    )
    drive_id = db.Column(db.Integer, db.ForeignKey("drives.id"), nullable=False, index=True)

    application_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(
        db.String(20), nullable=False, default="applied", index=True
    )  # applied/shortlisted/selected/rejected/placed

    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="uq_app_student_drive"),
    )

    student = db.relationship("Student", back_populates="applications")
    drive = db.relationship("Drive", back_populates="applications")
    placement = db.relationship("Placement", back_populates="application", uselist=False)


class Placement(db.Model):
    __tablename__ = "placements"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(
        db.Integer, db.ForeignKey("applications.id"), nullable=False, unique=True, index=True
    )

    offered_ctc = db.Column(db.Integer, nullable=True)
    joining_date = db.Column(db.Date, nullable=True)
    placed_on = db.Column(db.Date, nullable=False, default=date.today)

    application = db.relationship("Application", back_populates="placement")


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    try:
        uid = int(user_id)
    except ValueError:
        return None
    return db.session.get(User, uid)
