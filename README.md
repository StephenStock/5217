# 5217 Treasurer Aid

Local-first treasurer aid built with Flask, vanilla JavaScript, and SQLite, with spreadsheet fallback and handover as primary goals.

## What this repo contains

- Server-rendered admin app for members, dues, bookings, bank, cash, and reporting
- Local Windows launch flow via `start.bat`
- Optional hosted deploy flow via `deploy.bat`
- SQLite locally by default
- Project documentation under `docs/`

## Quick start

Run:

```bat
start.bat
```

This will:

1. Create a local virtual environment if needed
2. Install Flask
3. Use a local SQLite database on first run
4. Start the development server at `http://127.0.0.1:5000`

The app uses `TREASURER_DATABASE_URL` to decide which database to talk to. `start.bat` defaults to a local SQLite database in `%LOCALAPPDATA%\5217\Lodge.db`, which is now the preferred normal operating model.

If you need to point the app somewhere else, set `TREASURER_DATABASE_URL` before launching it.

`start.bat` prefers `py -3` when available, so whichever machine you use should have Python 3.10 or newer installed.

## Default seeded account

- Username: `lodgeadmin`, `treasurer`, `secretary`, or `helper`
- Password: `changeme`

The admin pages require login. These seeded accounts are only the starting point and should be changed as part of real setup.

## Documentation map

- [`docs/Runbook.md`](docs/Runbook.md): live environment, deploy flow, database, imports, and operations
- [`docs/roadmap.md`](docs/roadmap.md): product direction and current delivery phase
- [`docs/specs/`](docs/specs/): feature and business-rule documents
- [`docs/working-agreement.md`](docs/working-agreement.md): implementation workflow for the project

## Current product shape

- Internal users:
  - Treasurer
  - Admin/helper users
- Current operational areas:
  - Members and dues
  - Bank ledger and categorisation
  - Cash entry and settlement
  - Reporting and balances
- Public access:
  - public forms are optional and may remain in Microsoft Forms instead

## Product direction

- preferred direction: local-first treasurer's aid
- hosted AWS deployment: optional legacy path, not the main target
- continuity priority: exportability, handover, and spreadsheet fallback
- canonical operational reference: [`docs/Runbook.md`](docs/Runbook.md)
