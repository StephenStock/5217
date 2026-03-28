# Lodge Treasurer App

Starter web app for a lodge treasurer using Flask, SQLite, and vanilla JavaScript.

## What is included

- Flask application factory
- SQLite database schema with seeded sample data
- Server-rendered dashboard for members, dues, bookings, and messages
- `start.bat` launcher for local development

## Quick start

Run:

```bat
start.bat
```

This will:

1. Create a local virtual environment if needed
2. Install Flask
3. Initialize the SQLite database on first run
4. Start the development server at `http://127.0.0.1:5000`

The live SQLite database file is created at `%LOCALAPPDATA%\Treasurer\Lodge.db` by default. You can override that by setting the `TREASURER_DATABASE` environment variable before launching the app.

`start.bat` prefers `py -3` when available, so the other machine should have Python 3.10 or newer installed.

## Default seeded account

- Username: `treasurer`
- Password: `changeme`

This starter does not yet enforce authentication. The default account is seeded so we can add login next.

## Suggested next steps

- Add authentication and roles
- Add forms for members, dues, and events
- Build CSV export/import for handover and reporting
- Add payment workflow once the core record-keeping is solid

## Project planning

The project now includes a lightweight spec-driven docs structure:

- `docs/roadmap.md`
- `docs/working-agreement.md`
- `docs/specs/`
- `docs/sessions/`

This is intended to keep development in small, low-surprise slices.

Workbook analysis has also been captured in:

- `docs/specs/workbook-derived-requirements.md`
