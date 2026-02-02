from pathlib import Path

from flask import Flask

from .cli import init_db_command
from .config import Config
from .extensions import csrf, db, login_manager


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    # Ensure instance folder exists for SQLite DB + uploads.
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    # Extra protection against session hijacking (OK for this course project).
    login_manager.session_protection = "strong"

    from .main.routes import bp as main_bp

    app.register_blueprint(main_bp)

    from .auth.routes import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from .admin.routes import bp as admin_bp
    from .api.routes import bp as api_bp
    from .company.routes import bp as company_bp
    from .files.routes import bp as files_bp
    from .student.routes import bp as student_bp

    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(company_bp, url_prefix="/company")
    app.register_blueprint(files_bp, url_prefix="/files")
    app.register_blueprint(student_bp, url_prefix="/student")

    # CLI
    app.cli.add_command(init_db_command)

    return app
