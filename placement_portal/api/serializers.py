from __future__ import annotations

from datetime import date, datetime

from ..models import Application, Company, Drive, Notification, Placement, Student, User


def _iso(value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def user_to_dict(user: User) -> dict:
    data = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": bool(user.is_active),
        "created_at": _iso(user.created_at),
    }
    if user.role == "company" and user.company_profile:
        data["company_profile"] = company_to_dict(user.company_profile)
    if user.role == "student" and user.student_profile:
        data["student_profile"] = student_to_dict(user.student_profile)
    return data


def company_to_dict(company: Company) -> dict:
    return {
        "user_id": company.user_id,
        "company_name": company.company_name,
        "industry": company.industry,
        "hr_name": company.hr_name,
        "hr_email": company.hr_email,
        "hr_phone": company.hr_phone,
        "website": company.website,
        "description": company.description,
        "approval_status": company.approval_status,
        "is_blacklisted": bool(company.is_blacklisted),
        "created_at": _iso(company.created_at),
        "updated_at": _iso(company.updated_at),
    }


def student_to_dict(student: Student) -> dict:
    return {
        "user_id": student.user_id,
        "student_uid": student.student_uid,
        "full_name": student.full_name,
        "degree": student.degree,
        "department": student.department,
        "graduation_year": student.graduation_year,
        "cgpa": student.cgpa,
        "phone": student.phone,
        "skills": student.skills,
        "resume_available": bool(student.resume_path),
        "is_blacklisted": bool(student.is_blacklisted),
        "created_at": _iso(student.created_at),
        "updated_at": _iso(student.updated_at),
    }


def drive_to_dict(drive: Drive) -> dict:
    return {
        "id": drive.id,
        "company_id": drive.company_id,
        "company_name": drive.company.company_name if drive.company else None,
        "job_title": drive.job_title,
        "job_description": drive.job_description,
        "eligibility_criteria": drive.eligibility_criteria,
        "required_skills": drive.required_skills,
        "min_cgpa": drive.min_cgpa,
        "salary_min": drive.salary_min,
        "salary_max": drive.salary_max,
        "location": drive.location,
        "min_experience_years": drive.min_experience_years,
        "application_deadline": _iso(drive.application_deadline),
        "status": drive.status,
        "is_deleted": bool(drive.is_deleted),
        "created_at": _iso(drive.created_at),
        "updated_at": _iso(drive.updated_at),
    }


def application_to_dict(app: Application) -> dict:
    return {
        "id": app.id,
        "student_id": app.student_id,
        "student_name": app.student.full_name if app.student else None,
        "student_uid": app.student.student_uid if app.student else None,
        "drive_id": app.drive_id,
        "drive_title": app.drive.job_title if app.drive else None,
        "company_id": app.drive.company_id if (app.drive is not None) else None,
        "company_name": app.drive.company.company_name if (app.drive and app.drive.company) else None,
        "status": app.status,
        "application_date": _iso(app.application_date),
        "updated_at": _iso(app.updated_at),
        "placement_id": app.placement.id if app.placement else None,
    }


def placement_to_dict(placement: Placement) -> dict:
    return {
        "id": placement.id,
        "application_id": placement.application_id,
        "offered_ctc": placement.offered_ctc,
        "joining_date": _iso(placement.joining_date),
        "placed_on": _iso(placement.placed_on),
    }


def notification_to_dict(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "message": notification.message,
        "is_read": bool(notification.is_read),
        "created_at": _iso(notification.created_at),
    }

