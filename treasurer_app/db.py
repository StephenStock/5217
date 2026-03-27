import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


def ensure_instance_path(app) -> None:
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    schema_path = Path(__file__).with_name("schema.sql")
    db.executescript(schema_path.read_text(encoding="utf-8"))

    def due_status(subscription_due: float, subscription_paid: float, dining_due: float, dining_paid: float, member_code: str) -> str:
        outstanding = (subscription_due - subscription_paid) + (dining_due - dining_paid)
        if member_code in {"EXCLUDE", "DECEASED"}:
            return "written-off"
        if member_code == "RESIGNED" and outstanding > 0:
            return "written-off"
        if outstanding <= 0:
            return "paid"
        if subscription_paid > 0 or dining_paid > 0:
            return "part-paid"
        return "unpaid"

    db.execute(
        """
        INSERT INTO users (username, full_name, password_hash, role)
        VALUES (?, ?, ?, ?)
        """,
        ("treasurer", "Lodge Treasurer", generate_password_hash("changeme"), "treasurer"),
    )

    db.execute(
        """
        INSERT INTO reporting_periods (label, start_date, end_date, is_current)
        VALUES (?, ?, ?, ?)
        """,
        ("2025-26", "2025-09-01", "2026-08-31", 1),
    )

    db.executemany(
        """
        INSERT INTO member_types (
            code, description, subscription_rule, dining_rule,
            default_subscription_amount, default_dining_amount
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            ("FULL", "Full member", "standard", "annual_package", 200.00, 125.00),
            ("ND", "Non-diner", "standard", "none", 200.00, 0.00),
            ("PAYG", "Pay as you go dining", "standard", "payg", 200.00, 0.00),
            ("SEC", "Secretary", "exempt", "annual_package", 0.00, 125.00),
            ("EXCLUDE", "Excluded or unrecoverable", "manual", "manual", 200.00, 0.00),
            ("RESIGNED", "Resigned member", "manual", "manual", 200.00, 0.00),
            ("DECEASED", "Deceased member", "manual", "none", 200.00, 0.00),
            ("VISITOR", "Visitor", "none", "payg", 0.00, 0.00),
        ],
    )

    member_rows = [
        ("*Visitor", "VISITOR", None, 0.00, 0.00, 0.00, 0.00, ""),
        ("Awcock,David", "FULL", None, 200.00, 200.00, 125.00, 125.00, ""),
        ("Bradley Brown", "FULL", None, 120.00, 120.00, 75.00, 75.00, ""),
        ("Chipperfield,David", "ND", None, 200.00, 200.00, 0.00, 0.00, ""),
        ("Coleridge,Ashley", "SEC", None, 0.00, 0.00, 0.00, 0.00, ""),
        ("Coleridge-Humphries,Connor", "ND", None, 200.00, 200.00, 150.00, 150.00, ""),
        ("Connolly,P.J", "EXCLUDE", None, 200.00, 0.00, 0.00, 0.00, "Spoke to his son, he has dementia, so this money is lost"),
        ("Featherstone,Allen", "ND", None, 200.00, 200.00, 0.00, 0.00, ""),
        ("Fulford,Len", "FULL", None, 200.00, 200.00, 125.00, 125.00, ""),
        ("Gillam,Mark", "PAYG", None, 200.00, 200.00, 0.00, 0.00, ""),
        ("Higgins, Nicolas", "FULL", None, 200.00, 200.00, 125.00, 125.00, ""),
        ("Holloway,Ian", "RESIGNED", None, 200.00, 0.00, 0.00, 0.00, "Resigned"),
        ("James,Ian", "PAYG", None, 400.00, 300.00, 0.00, 0.00, ""),
        ("Jess, Matthew", "FULL", None, 200.00, 200.00, 125.00, 125.00, ""),
        ("Marshall,Arthur", "ND", None, 200.00, 200.00, 0.00, 0.00, ""),
        ("Matondo, Herve", "RESIGNED", None, 200.00, 0.00, 0.00, 0.00, "Resigning - write off"),
        ("Moss,Peter", "FULL", None, 149.40, 149.40, 93.60, 93.60, ""),
        ("Mullender,Ray", "PAYG", None, 200.00, 200.00, 0.00, 0.00, ""),
        ("O'Brien,Keith", "FULL", None, 200.00, 200.00, 125.00, 125.00, ""),
        ("Pavey, Shaun", "FULL", None, 240.00, 0.00, 0.00, 0.00, "Reminder sent 4th Jan"),
        ("Peacock,Steve", "FULL", None, 200.00, 200.00, 125.00, 125.00, ""),
        ("Petchey,Ken", "ND", None, 200.00, 0.00, 0.00, 0.00, "Reminder sent 4th Jan"),
        ("Phillips,Andrew", "FULL", None, 200.00, 200.00, 125.00, 125.00, ""),
        ("Porter,John", "RESIGNED", None, 200.00, 200.00, 125.00, 125.00, "Arrears from last year, nothing owing now"),
        ("South,Ray", "DECEASED", None, 200.00, 0.00, 0.00, 0.00, "Write off of course"),
        ("Stock,Stephen", "FULL", None, 200.00, 200.00, 125.00, 125.00, ""),
        ("Stribling,Martyn", "ND", None, 200.00, 200.00, 0.00, 0.00, ""),
        ("Walden,Connor", "FULL", None, 200.00, 200.00, 125.00, 125.00, ""),
        ("Walden,Mark", "FULL", None, 200.00, 200.00, 125.00, 125.00, ""),
        ("Withey, Graham", "FULL", None, 200.00, 200.00, 125.00, 125.00, ""),
    ]

    member_type_ids = {
        row["code"]: row["id"]
        for row in db.execute("SELECT id, code FROM member_types").fetchall()
    }

    db.executemany(
        """
        INSERT INTO members (
            membership_number, full_name, member_type_id, email, phone, status, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                f"M{index:03d}",
                name,
                member_type_ids[member_code],
                None,
                None,
                (
                    "visitor" if member_code == "VISITOR"
                    else "excluded" if member_code == "EXCLUDE"
                    else "resigned" if member_code == "RESIGNED"
                    else "deceased" if member_code == "DECEASED"
                    else "active"
                ),
                notes,
            )
            for index, (name, member_code, _pp_subs, subs_due, subs_paid, dining_due, dining_paid, notes)
            in enumerate(member_rows, start=1)
        ],
    )

    db.executemany(
        """
        INSERT INTO dues (
            member_id, reporting_period_id, year,
            subscription_due, subscription_paid, dining_due, dining_paid, status, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                index,
                1,
                2026,
                subs_due,
                subs_paid,
                dining_due,
                dining_paid,
                due_status(subs_due, subs_paid, dining_due, dining_paid, member_code),
                notes,
            )
            for index, (_name, member_code, _pp_subs, subs_due, subs_paid, dining_due, dining_paid, notes)
            in enumerate(member_rows, start=1)
        ],
    )

    db.executemany(
        """
        INSERT INTO subscription_charges (
            member_id, reporting_period_id, charge_type, description, amount, due_date, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                index,
                1,
                "annual",
                "Annual lodge subscription",
                subs_due,
                "2025-10-01",
                notes,
            )
            for index, (_name, member_code, _pp_subs, subs_due, _subs_paid, _dining_due, _dining_paid, notes)
            in enumerate(member_rows, start=1)
            if member_code != "VISITOR" and subs_due > 0
        ],
    )

    db.execute(
        """
        INSERT INTO events (title, event_date, meal_name, meal_price, booking_deadline, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "April Lodge Dinner",
            "2026-04-21",
            "Three-course festive board",
            22.50,
            "2026-04-17",
            "Members can book meals and note dietary requirements.",
        ),
    )

    db.executemany(
        """
        INSERT INTO dining_charges (
            member_id, event_id, reporting_period_id, description, amount, status, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                index,
                1,
                1,
                "Annual dining balance",
                dining_due,
                "paid" if dining_due <= dining_paid else ("part-paid" if dining_paid > 0 else "due"),
                notes,
            )
            for index, (_name, member_code, _pp_subs, _subs_due, _subs_paid, dining_due, dining_paid, notes)
            in enumerate(member_rows, start=1)
            if member_code != "VISITOR" and dining_due > 0
        ],
    )

    db.executemany(
        """
        INSERT INTO bookings (event_id, member_id, seats, dietary_notes, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (1, 2, 1, "", "confirmed"),
            (1, 10, 1, "", "confirmed"),
        ],
    )

    db.executemany(
        """
        INSERT INTO payments (
            member_id, reporting_period_id, payment_date, payment_method, reference,
            total_amount, subscription_amount, dining_amount, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                index,
                1,
                "2025-09-10",
                "bank",
                f"IMPORT-{index:03d}",
                subs_paid + dining_paid,
                subs_paid,
                dining_paid,
                notes,
            )
            for index, (_name, member_code, _pp_subs, _subs_due, subs_paid, _dining_due, dining_paid, notes)
            in enumerate(member_rows, start=1)
            if member_code != "VISITOR" and (subs_paid + dining_paid) > 0
        ],
    )

    db.execute(
        """
        INSERT INTO messages (sender_name, sender_role, subject, body, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "Secretary",
            "secretary",
            "Agenda reminder",
            "Please confirm the dues report is ready for the next committee meeting.",
            "open",
        ),
    )

    db.commit()


def init_app(app) -> None:
    @app.cli.command("init-db")
    def init_db_command() -> None:
        init_db()
        print("Initialized the database.")
