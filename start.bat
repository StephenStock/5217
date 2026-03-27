@echo off
cd /d "%~dp0"

for /f "usebackq delims=" %%P in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$root = [Regex]::Escape((Get-Location).Path); Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(python|pythonw)\.exe$' -and $_.CommandLine -and $_.CommandLine -match $root -and ($_.CommandLine -match 'flask(\.exe)?\s+--app\s+app\s+run' -or $_.CommandLine -match 'app\.py') } | Select-Object -ExpandProperty ProcessId"`) do (
    taskkill /PID %%P /F >nul 2>nul
)

where python >nul 2>nul
if not %errorlevel%==0 (
    echo Python was not found on PATH.
    echo Install Python 3 for Windows from https://www.python.org/downloads/
    pause
    goto :eof
)

python -c "import sys; print(sys.version)" >nul 2>nul
if not %errorlevel%==0 (
    echo Python 3 is not available.
    echo Install Python 3 for Windows from https://www.python.org/downloads/
    pause
    goto :eof
)

if not exist ".venv" (
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if not %errorlevel%==0 (
    echo Failed to install Python packages.
    pause
    goto :eof
)

python -c "import sqlite3, sys; db = sqlite3.connect(r'instance\Lodge.db'); cols = [row[1] for row in db.execute(\"PRAGMA table_info(members)\")]; sys.exit(0 if 'membership_number' in cols else 1)" >nul 2>nul
if not %errorlevel%==0 (
    if exist "instance\Lodge.db" del /q "instance\Lodge.db"
    flask --app app init-db
    if not %errorlevel%==0 (
        echo Failed to initialize the database.
        pause
        goto :eof
    )
)

if not exist "instance\Lodge.db" (
    flask --app app init-db
    if not %errorlevel%==0 (
        echo Failed to initialize the database.
        pause
        goto :eof
    )
)

start "" http://127.0.0.1:5000/
flask --app app run --debug
