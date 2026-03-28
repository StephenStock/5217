import re
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


WORKBOOK_BANK_SHEET = "Bank"
WORKBOOK_CANDIDATES = (
    "Accounts 2025-26.xlsx",
    "LodgeAccounts_Template.xlsx",
)

BANK_CATEGORY_DEFINITIONS = [
    ("CASH", "Cash", "in", 10),
    ("PRE_SUBS", "Pre-Subs", "in", 20),
    ("PRE_DINING", "Pre-Dining", "in", 30),
    ("SUBS", "Subs", "in", 40),
    ("DINING", "Dining", "in", 50),
    ("VISITOR", "Visitor", "in", 60),
    ("INITIATION", "Initiation", "in", 70),
    ("SUMUP", "SumUp", "in", 80),
    ("GAVEL", "Gavel", "in", 90),
    ("DONATIONS_IN", "Donations", "in", 100),
    ("CHAPTER_LOI", "Chapter LOI", "in", 110),
    ("LOI", "LOI", "in", 120),
    ("RELIEF", "Relief", "out", 130),
    ("DONATIONS_OUT", "Donations", "out", 140),
    ("UGLE", "UGLE", "out", 150),
    ("PGLE", "PGLE", "out", 160),
    ("ORSETT", "Orsett", "out", 170),
    ("WOOLMKT", "WoolMkt", "out", 180),
    ("CATERER", "Caterer", "out", 190),
    ("BANK_CHARGES", "Bank Charges", "out", 200),
    ("WIDOWS", "Widows", "out", 210),
]

BANK_COLUMN_CATEGORY_CODES = {
    "L": "CASH",
    "M": "PRE_SUBS",
    "N": "PRE_DINING",
    "O": "SUBS",
    "P": "DINING",
    "Q": "VISITOR",
    "R": "INITIATION",
    "S": "SUMUP",
    "T": "GAVEL",
    "U": "DONATIONS_IN",
    "V": "CHAPTER_LOI",
    "W": "LOI",
    "Z": "RELIEF",
    "AA": "DONATIONS_OUT",
    "AB": "UGLE",
    "AC": "PGLE",
    "AD": "ORSETT",
    "AE": "WOOLMKT",
    "AF": "CATERER",
    "AG": "BANK_CHARGES",
    "AH": "WIDOWS",
}

_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_NS = {"main": _MAIN_NS, "rel": _REL_NS, "pkgrel": _PKG_REL_NS}


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


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _candidate_workbook_paths() -> list[Path]:
    root = _project_root()
    return [root / name for name in WORKBOOK_CANDIDATES]


def _find_existing_workbook() -> Path | None:
    for path in _candidate_workbook_paths():
        if path.exists():
            return path
    return None


def _excel_serial_to_iso_date(raw_value: str | None) -> str | None:
    if not raw_value:
        return None
    serial = int(float(raw_value))
    return (date(1899, 12, 30) + timedelta(days=serial)).isoformat()


def _to_amount(raw_value: str | None) -> float:
    if raw_value in (None, ""):
        return 0.0
    return round(float(raw_value), 2)


def _load_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    shared_strings: list[str] = []
    path = "xl/sharedStrings.xml"
    if path not in archive.namelist():
        return shared_strings

    root = ET.fromstring(archive.read(path))
    for item in root.findall(f"{{{_MAIN_NS}}}si"):
        shared_strings.append("".join(node.text or "" for node in item.iter(f"{{{_MAIN_NS}}}t")))
    return shared_strings


def _get_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")

    if cell_type == "inlineStr":
        text_node = cell.find(f"{{{_MAIN_NS}}}is")
        return "" if text_node is None else "".join(node.text or "" for node in text_node.iter(f"{{{_MAIN_NS}}}t"))

    value_node = cell.find(f"{{{_MAIN_NS}}}v")
    if value_node is None or value_node.text is None:
        return ""

    if cell_type == "s":
        return shared_strings[int(value_node.text)]

    return value_node.text


def _sheet_target_by_name(archive: zipfile.ZipFile, sheet_name: str) -> str | None:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relationship_map = {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in relationships.findall(f"{{{_PKG_REL_NS}}}Relationship")
    }

    sheets = workbook.find("main:sheets", _NS)
    if sheets is None:
        return None

    for sheet in sheets.findall("main:sheet", _NS):
        if sheet.attrib.get("name") == sheet_name:
            relationship_id = sheet.attrib.get(f"{{{_REL_NS}}}id")
            if relationship_id:
                return relationship_map.get(relationship_id)
    return None


def _read_sheet_rows(workbook_path: Path, sheet_name: str) -> list[tuple[int, dict[str, str]]]:
    with zipfile.ZipFile(workbook_path) as archive:
        target = _sheet_target_by_name(archive, sheet_name)
        if target is None:
            return []

        shared_strings = _load_shared_strings(archive)
        sheet_xml = ET.fromstring(archive.read(f"xl/{target}"))
        sheet_data = sheet_xml.find(f"{{{_MAIN_NS}}}sheetData")
        if sheet_data is None:
            return []

        rows: list[tuple[int, dict[str, str]]] = []
        for row in sheet_data.findall(f"{{{_MAIN_NS}}}row"):
            row_number = int(row.attrib["r"])
            values: dict[str, str] = {}
            for cell in row.findall(f"{{{_MAIN_NS}}}c"):
                reference = cell.attrib.get("r", "")
                column = re.match(r"[A-Z]+", reference)
                if column is None:
                    continue
                values[column.group(0)] = _get_cell_value(cell, shared_strings)
            rows.append((row_number, values))
        return rows


def seed_ledger_categories(db: sqlite3.Connection) -> None:
    db.executemany(
        """
        INSERT OR IGNORE INTO ledger_categories (code, display_name, direction, sort_order)
        VALUES (?, ?, ?, ?)
        """,
        BANK_CATEGORY_DEFINITIONS,
    )


def ensure_financial_tables(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS ledger_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            direction TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS bank_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporting_period_id INTEGER NOT NULL,
            transaction_date TEXT,
            details TEXT NOT NULL,
            transaction_type TEXT,
            money_in REAL NOT NULL DEFAULT 0,
            money_out REAL NOT NULL DEFAULT 0,
            running_balance REAL,
            is_opening_balance INTEGER NOT NULL DEFAULT 0,
            source_workbook TEXT,
            source_sheet TEXT,
            source_row_number INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reporting_period_id) REFERENCES reporting_periods (id),
            UNIQUE (source_workbook, source_sheet, source_row_number)
        );

        CREATE TABLE IF NOT EXISTS bank_transaction_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_transaction_id INTEGER NOT NULL,
            ledger_category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bank_transaction_id) REFERENCES bank_transactions (id) ON DELETE CASCADE,
            FOREIGN KEY (ledger_category_id) REFERENCES ledger_categories (id)
        );

        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporting_period_id INTEGER NOT NULL,
            meeting_key TEXT NOT NULL UNIQUE,
            meeting_name TEXT NOT NULL,
            meeting_date TEXT,
            meeting_type TEXT NOT NULL DEFAULT 'Regular',
            sort_order INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reporting_period_id) REFERENCES reporting_periods (id)
        );

        CREATE TABLE IF NOT EXISTS cashbook_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporting_period_id INTEGER NOT NULL,
            meeting_key TEXT NOT NULL CHECK (meeting_key IN ('SEPTEMBER', 'NOVEMBER', 'JANUARY', 'MARCH', 'MAY')),
            entry_type TEXT NOT NULL,
            entry_name TEXT NOT NULL,
            member_id INTEGER,
            ledger_category_id INTEGER,
            money_in REAL NOT NULL DEFAULT 0,
            money_out REAL NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reporting_period_id) REFERENCES reporting_periods (id),
            FOREIGN KEY (member_id) REFERENCES members (id),
            FOREIGN KEY (ledger_category_id) REFERENCES ledger_categories (id)
        );

        CREATE INDEX IF NOT EXISTS idx_bank_transactions_date ON bank_transactions (transaction_date);
        CREATE INDEX IF NOT EXISTS idx_bank_transactions_reporting_period_id ON bank_transactions (reporting_period_id);
        CREATE INDEX IF NOT EXISTS idx_bank_transaction_allocations_transaction_id ON bank_transaction_allocations (bank_transaction_id);
        CREATE INDEX IF NOT EXISTS idx_bank_transaction_allocations_category_id ON bank_transaction_allocations (ledger_category_id);
        CREATE INDEX IF NOT EXISTS idx_meetings_reporting_period_id ON meetings (reporting_period_id);
        CREATE INDEX IF NOT EXISTS idx_meetings_sort_order ON meetings (sort_order);
        CREATE INDEX IF NOT EXISTS idx_cashbook_entries_meeting_key ON cashbook_entries (meeting_key);
        """
    )


def _category_id_map(db: sqlite3.Connection) -> dict[str, int]:
    return {
        row["code"]: row["id"]
        for row in db.execute("SELECT id, code FROM ledger_categories").fetchall()
    }


def _dues_status(
    subscription_due: float,
    subscription_paid: float,
    dining_due: float,
    dining_paid: float,
    member_code: str,
) -> str:
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


def seed_meeting_schedule(db: sqlite3.Connection, reporting_period_id: int = 1) -> None:
    meeting_rows = [
        ("SEPTEMBER", "September Meeting", "2025-09-15", "Regular", 1, ""),
        ("NOVEMBER", "November Meeting", "2025-11-17", "Regular", 2, ""),
        ("JANUARY", "January Meeting", "2026-01-19", "Regular", 3, ""),
        ("MARCH", "March Meeting", "2026-03-16", "Regular", 4, ""),
        ("MAY", "Installation Meeting", "2026-05-18", "Installation", 5, ""),
    ]

    db.executemany(
        """
        INSERT OR IGNORE INTO meetings (
            reporting_period_id, meeting_key, meeting_name, meeting_date, meeting_type, sort_order, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (reporting_period_id, key, name, meeting_date, meeting_type, sort_order, notes)
            for key, name, meeting_date, meeting_type, sort_order, notes in meeting_rows
        ],
    )


def import_bank_transactions_from_workbook(
    db: sqlite3.Connection,
    reporting_period_id: int,
    workbook_path: Path,
) -> int:
    rows = _read_sheet_rows(workbook_path, WORKBOOK_BANK_SHEET)
    if not rows:
        return 0

    category_ids = _category_id_map(db)
    imported = 0

    for row_number, row in rows[1:]:
        row_label = row.get("A", "").strip()
        details = row.get("B", "").strip()
        transaction_type = row.get("C", "").strip()

        if row_label == "TOTALS" or details == "TOTALS":
            break

        if not details and not transaction_type and not row.get("D") and not row.get("E"):
            continue

        transaction_date = _excel_serial_to_iso_date(row.get("A"))
        money_in = _to_amount(row.get("D"))
        money_out = _to_amount(row.get("E"))
        running_balance = row.get("F")

        cursor = db.execute(
            """
            INSERT OR IGNORE INTO bank_transactions (
                reporting_period_id,
                transaction_date,
                details,
                transaction_type,
                money_in,
                money_out,
                running_balance,
                is_opening_balance,
                source_workbook,
                source_sheet,
                source_row_number
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reporting_period_id,
                transaction_date,
                details or "Imported transaction",
                transaction_type or None,
                money_in,
                money_out,
                float(running_balance) if running_balance not in (None, "") else None,
                1 if details == "Opening Balance" else 0,
                workbook_path.name,
                WORKBOOK_BANK_SHEET,
                row_number,
            ),
        )
        if cursor.rowcount == 0:
            continue
        bank_transaction_id = cursor.lastrowid

        for column, category_code in BANK_COLUMN_CATEGORY_CODES.items():
            amount = _to_amount(row.get(column))
            if amount == 0:
                continue
            db.execute(
                """
                INSERT INTO bank_transaction_allocations (
                    bank_transaction_id, ledger_category_id, amount
                )
                VALUES (?, ?, ?)
                """,
                (bank_transaction_id, category_ids[category_code], amount),
            )

        imported += 1

    return imported


def replace_bank_transaction_allocations(
    db: sqlite3.Connection,
    bank_transaction_id: int,
    allocations: list[tuple[int, float]],
) -> None:
    db.execute(
        "DELETE FROM bank_transaction_allocations WHERE bank_transaction_id = ?",
        (bank_transaction_id,),
    )
    db.executemany(
        """
        INSERT INTO bank_transaction_allocations (bank_transaction_id, ledger_category_id, amount)
        VALUES (?, ?, ?)
        """,
        [
            (bank_transaction_id, ledger_category_id, amount)
            for ledger_category_id, amount in allocations
        ],
    )


def import_bank_transactions(db: sqlite3.Connection, reporting_period_id: int = 1) -> int:
    ensure_financial_tables(db)
    seed_ledger_categories(db)
    workbook_path = _find_existing_workbook()
    if workbook_path is None:
        return 0
    return import_bank_transactions_from_workbook(db, reporting_period_id, workbook_path)


def seed_bank_transactions_from_payments(
    db: sqlite3.Connection,
    reporting_period_id: int,
) -> int:
    category_ids = _category_id_map(db)
    payment_rows = db.execute(
        """
        SELECT
            p.id,
            p.payment_date,
            p.payment_method,
            p.reference,
            p.total_amount,
            p.subscription_amount,
            p.dining_amount,
            m.full_name
        FROM payments p
        JOIN members m ON m.id = p.member_id
        WHERE p.reporting_period_id = ?
        ORDER BY p.payment_date, p.id
        """,
        (reporting_period_id,),
    ).fetchall()

    for payment in payment_rows:
        cursor = db.execute(
            """
            INSERT INTO bank_transactions (
                reporting_period_id,
                transaction_date,
                details,
                transaction_type,
                money_in,
                money_out,
                source_workbook,
                source_sheet,
                source_row_number,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reporting_period_id,
                payment["payment_date"],
                f'{payment["full_name"]} payment',
                payment["payment_method"],
                float(payment["total_amount"]),
                0.0,
                "system",
                "payments",
                int(payment["id"]),
                payment["reference"],
            ),
        )
        bank_transaction_id = cursor.lastrowid

        if payment["subscription_amount"] > 0:
            db.execute(
                """
                INSERT INTO bank_transaction_allocations (
                    bank_transaction_id, ledger_category_id, amount
                )
                VALUES (?, ?, ?)
                """,
                (bank_transaction_id, category_ids["SUBS"], float(payment["subscription_amount"])),
            )
        if payment["dining_amount"] > 0:
            db.execute(
                """
                INSERT INTO bank_transaction_allocations (
                    bank_transaction_id, ledger_category_id, amount
                )
                VALUES (?, ?, ?)
                """,
                (bank_transaction_id, category_ids["DINING"], float(payment["dining_amount"])),
            )

    return len(payment_rows)


def seed_bank_ledger(db: sqlite3.Connection, reporting_period_id: int = 1) -> int:
    if db.execute("SELECT COUNT(*) AS total FROM bank_transactions").fetchone()["total"] > 0:
        return 0

    workbook_path = _find_existing_workbook()
    if workbook_path is not None:
        imported = import_bank_transactions_from_workbook(db, reporting_period_id, workbook_path)
        if imported > 0:
            return imported

    return seed_bank_transactions_from_payments(db, reporting_period_id)


def init_db() -> None:
    db = get_db()
    schema_path = Path(__file__).with_name("schema.sql")
    db.executescript(schema_path.read_text(encoding="utf-8"))

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

    seed_meeting_schedule(db, reporting_period_id=1)

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
                _dues_status(subs_due, subs_paid, dining_due, dining_paid, member_code),
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

    ensure_financial_tables(db)
    seed_ledger_categories(db)
    seed_bank_ledger(db, reporting_period_id=1)

    db.commit()


def init_app(app) -> None:
    @app.cli.command("init-db")
    def init_db_command() -> None:
        init_db()
        print("Initialized the database.")
