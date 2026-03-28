from pathlib import Path

from flask import Flask

from .db import close_db, ensure_financial_tables, ensure_instance_path, get_db, init_app, seed_ledger_categories, seed_meeting_schedule
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

    with app.app_context():
        db = get_db()
        ensure_financial_tables(db)
        seed_ledger_categories(db)
        has_reporting_periods = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='reporting_periods'"
        ).fetchone()
        if has_reporting_periods:
            period_count = db.execute("SELECT COUNT(*) AS total FROM reporting_periods").fetchone()["total"]
            if period_count > 0:
                seed_meeting_schedule(db, reporting_period_id=1)
        db.commit()

    return app
