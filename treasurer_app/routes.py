from flask import Blueprint, render_template

from .db import get_db


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def dashboard():
    db = get_db()

    stats = {
        "members": db.execute("SELECT COUNT(*) AS total FROM members").fetchone()["total"],
        "events": db.execute("SELECT COUNT(*) AS total FROM events").fetchone()["total"],
        "open_messages": db.execute(
            "SELECT COUNT(*) AS total FROM messages WHERE status = 'open'"
        ).fetchone()["total"],
        "dues_outstanding": db.execute(
            """
            SELECT COALESCE(
                SUM((subscription_due - subscription_paid) + (dining_due - dining_paid)),
                0
            ) AS total
            FROM dues
            WHERE subscription_due > subscription_paid
               OR dining_due > dining_paid
            """
        ).fetchone()["total"],
    }

    recent_members = db.execute(
        """
        SELECT m.membership_number, m.full_name, mt.code AS member_type, m.email, m.status
        FROM members m
        LEFT JOIN member_types mt ON mt.id = m.member_type_id
        ORDER BY full_name
        LIMIT 5
        """
    ).fetchall()

    dues = db.execute(
        """
        SELECT
            m.full_name,
            d.year,
            d.subscription_due,
            d.subscription_paid,
            d.dining_due,
            d.dining_paid,
            (d.subscription_due - d.subscription_paid) AS subscription_outstanding,
            (d.dining_due - d.dining_paid) AS dining_outstanding,
            d.status
        FROM dues d
        JOIN members m ON m.id = d.member_id
        ORDER BY d.status DESC, m.full_name
        """
    ).fetchall()

    upcoming_events = db.execute(
        """
        SELECT id, title, event_date, meal_name, meal_price, booking_deadline, notes
        FROM events
        ORDER BY event_date
        """
    ).fetchall()

    bookings = db.execute(
        """
        SELECT e.title, m.full_name, b.seats, b.dietary_notes, b.status
        FROM bookings b
        JOIN events e ON e.id = b.event_id
        JOIN members m ON m.id = b.member_id
        ORDER BY e.event_date, m.full_name
        """
    ).fetchall()

    messages = db.execute(
        """
        SELECT sender_name, sender_role, subject, body, status, created_at
        FROM messages
        ORDER BY created_at DESC
        """
    ).fetchall()

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_members=recent_members,
        dues=dues,
        upcoming_events=upcoming_events,
        bookings=bookings,
        messages=messages,
    )
