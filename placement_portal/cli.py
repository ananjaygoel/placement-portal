import click
from flask import current_app

from .extensions import db
from .models import Admin, User


@click.command("init-db")
def init_db_command() -> None:
    """Create all tables and seed the predefined admin user."""
    db.create_all()

    admin_email = current_app.config["ADMIN_EMAIL"]
    admin_password = current_app.config["ADMIN_PASSWORD"]

    existing_user = User.query.filter_by(email=admin_email).first()
    created_user = False
    if existing_user is None:
        admin = User(email=admin_email, role="admin")
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()  # commit to get admin.id
        existing_user = admin
        created_user = True

    existing_admin = Admin.query.filter_by(user_id=existing_user.id).first()
    if existing_admin is None:
        db.session.add(Admin(user_id=existing_user.id))
        db.session.commit()

    if created_user:
        click.echo(f"Seeded admin user: {admin_email}")
    else:
        click.echo("Admin user already seeded.")

    click.echo("Database initialized.")
