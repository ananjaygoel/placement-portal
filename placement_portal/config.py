import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Allow override via DATABASE_URL (used by some hosting platforms).
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{INSTANCE_DIR / 'placement_portal.sqlite3'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Predefined admin (override via env if needed)
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "23f2001063@ds.study.iitm.ac.in")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "IITMBS")

    # Uploads (used later for resumes)
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(INSTANCE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))

