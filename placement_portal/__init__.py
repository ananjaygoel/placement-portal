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

    from .main.routes import bp as main_bp

    app.register_blueprint(main_bp)

    # Auth blueprint will be added in the next milestone.
    # Keeping this import here avoids circular import issues later.
    from .auth.routes import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    # CLI
    app.cli.add_command(init_db_command)

    return app

