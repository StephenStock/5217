PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS dining_charges;
DROP TABLE IF EXISTS subscription_charges;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS dues;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS members;
DROP TABLE IF EXISTS member_types;
DROP TABLE IF EXISTS reporting_periods;
DROP TABLE IF EXISTS users;

PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reporting_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE member_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    subscription_rule TEXT NOT NULL,
    dining_rule TEXT NOT NULL,
    default_subscription_amount REAL NOT NULL DEFAULT 0,
    default_dining_amount REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    membership_number TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    member_type_id INTEGER,
    email TEXT,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_type_id) REFERENCES member_types (id)
);

CREATE TABLE dues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    reporting_period_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    subscription_due REAL NOT NULL DEFAULT 0,
    subscription_paid REAL NOT NULL DEFAULT 0,
    dining_due REAL NOT NULL DEFAULT 0,
    dining_paid REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'unpaid',
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members (id),
    FOREIGN KEY (reporting_period_id) REFERENCES reporting_periods (id)
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    event_date TEXT NOT NULL,
    meal_name TEXT,
    meal_price REAL NOT NULL DEFAULT 0,
    booking_deadline TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    seats INTEGER NOT NULL DEFAULT 1,
    dietary_notes TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events (id),
    FOREIGN KEY (member_id) REFERENCES members (id)
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_name TEXT NOT NULL,
    sender_role TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subscription_charges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    reporting_period_id INTEGER NOT NULL,
    charge_type TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0,
    due_date TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members (id),
    FOREIGN KEY (reporting_period_id) REFERENCES reporting_periods (id)
);

CREATE TABLE dining_charges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    event_id INTEGER,
    reporting_period_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'due',
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members (id),
    FOREIGN KEY (event_id) REFERENCES events (id),
    FOREIGN KEY (reporting_period_id) REFERENCES reporting_periods (id)
);

CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    reporting_period_id INTEGER NOT NULL,
    payment_date TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    reference TEXT,
    total_amount REAL NOT NULL DEFAULT 0,
    subscription_amount REAL NOT NULL DEFAULT 0,
    dining_amount REAL NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members (id),
    FOREIGN KEY (reporting_period_id) REFERENCES reporting_periods (id)
);

CREATE INDEX idx_members_member_type_id ON members (member_type_id);
CREATE INDEX idx_dues_member_id ON dues (member_id);
CREATE INDEX idx_dues_reporting_period_id ON dues (reporting_period_id);
CREATE INDEX idx_subscription_charges_member_id ON subscription_charges (member_id);
CREATE INDEX idx_dining_charges_member_id ON dining_charges (member_id);
CREATE INDEX idx_payments_member_id ON payments (member_id);
CREATE INDEX idx_bookings_event_id ON bookings (event_id);
CREATE INDEX idx_messages_status ON messages (status);
