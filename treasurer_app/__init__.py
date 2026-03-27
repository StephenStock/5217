from pathlib import Path

from flask import Flask

from .db import close_db, ensure_instance_path, init_app
from .routes import main_bp


def create_app(test_config: dict | None = None) -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )
    app.config.from_mapping(
        SECRET_KEY="change-me",
        DATABASE=str(Path(app.instance_path) / "Lodge.db"),
    )

    if test_config is not None:
        app.config.update(test_config)

    ensure_instance_path(app)
    init_app(app)
    app.teardown_appcontext(close_db)
    app.register_blueprint(main_bp)

    return app
