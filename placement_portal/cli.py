import click
from flask import current_app

from .extensions import db
from .models import User


@click.command("init-db")
def init_db_command() -> None:
    """Create all tables and seed the predefined admin user."""
    db.create_all()

    admin_email = current_app.config["ADMIN_EMAIL"]
    admin_password = current_app.config["ADMIN_PASSWORD"]

    existing = User.query.filter_by(email=admin_email).first()
    if existing is None:
        admin = User(email=admin_email, role="admin")
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Seeded admin user: {admin_email}")
    else:
        click.echo("Admin user already seeded.")

    click.echo("Database initialized.")

