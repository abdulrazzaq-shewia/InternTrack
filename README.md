# InternTrack

A local web application for managing internship applications, interviews, and notes.

**Student:** Abdulrazzaq Shewia  
**Course:** CIS 375, Software Engineering I  
**Professor:** Dr. Raef Aidibi  
**Final deadline:** November 1, 2026

## Start on Windows (recommended)

1. Install **Python 3.12 or later** from https://www.python.org/downloads/. Enable the Python launcher during installation.
2. Extract the entire ZIP into a normal writable folder such as `Documents\InternTrack`. Do not run it from inside the ZIP.
3. Open the extracted `InternTrack` folder and double-click **start_windows.bat**.
4. On the first run, wait for dependencies to install. Internet access is required for installation.
5. Leave the terminal window open and open **http://127.0.0.1:5000** in your browser.
6. Select **Create an account**, choose your own username and a password of at least 10 characters, and add your first application.
7. Press **Ctrl+C** in the terminal to stop. Double-click the launcher again to restart. Your saved records remain available.

Python 3.12 on Linux was used for automated validation. The Windows launcher is included but has not been executed on a Windows machine here.

### Manual Windows setup (PowerShell)

Open a terminal in the extracted folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

No PowerShell activation script or execution-policy change is needed.

### macOS / Linux

```bash
sh start_mac_linux.sh
```

Or:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
```

## Optional fictional demo data

The application starts empty. Real applications are not included. To create a **separate** sample account, stop the server with Ctrl+C and run:

Windows:

```powershell
.\.venv\Scripts\python.exe -m flask --app run:app seed-demo
```

macOS / Linux:

```bash
.venv/bin/python -m flask --app run:app seed-demo
```

Choose and confirm a demo password when prompted (input is hidden). The default username is `demo`. Start the server again and sign in with that username and your chosen password. Seven clearly fictional applications are added. There is no built-in password. Running the command again with the same username will refuse without changing existing data. To create another separate demo account, add `--username demo2`.

## How to use it

- **Overview:** global status counts for your account, your application list, and the next five future interviews.
- **Add application:** company, position, application date, and status are required. Job link, notes, and interview date/time are optional.
- **Statuses:** Applied, Interview, Offer, Rejected, Withdrawn.
- **Interview dates:** enter your local date and time. Only future records with **Interview** status appear in “Next conversations.” Start the app on your own computer so its clock and time zone match yours. Automatic time-zone conversion is not implemented.
- **Search:** matches company or position, ignoring case. Search text is treated literally. Choose a status and click **Apply**; use **Clear** to remove filters.
- **Status cards:** click a card to filter the list. Counts always describe the entire account, even with a filtered list.
- **View/edit:** open the company name or arrow, then choose **Edit application**.
- **Delete:** open a record, choose **Delete application**, and confirm on a separate page. The record is permanently removed.
- **Sign out:** ends the current session. Another user can create an account and will see a separate empty workspace.

## Data and configuration

The first launch automatically creates tables and a random persistent local session secret:

- `instance/interntrack.db`: SQLite records and password hashes.
- `instance/secret.key`: local session-signing secret. Keep it private and out of Git.

Back up the `instance` directory **while the application is stopped**. Restore that directory into the same location while stopped, then restart. Losing the database loses the records. Losing the secret logs out existing sessions but does not delete records.

You may supply `INTERNTRACK_SECRET_KEY` as an environment variable instead of the generated file. Use a long random value and keep it private. `init-db` creates missing tables and preserves records; it is not a schema migration command.

## Run the tests

Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

macOS / Linux:

```bash
.venv/bin/python -m pytest -q
```

Tests create isolated temporary databases and leave normal application data unchanged. See `docs/test-results.txt`, `docs/performance-results.json`, and `docs/TEST_PLAN.md`. To repeat timing checks on macOS/Linux:

```bash
PYTHONPATH=.:tests .venv/bin/python tests/benchmark.py
```

To run the same benchmark in PowerShell:

```powershell
$env:PYTHONPATH = ".;tests"
.\.venv\Scripts\python.exe tests\benchmark.py
Remove-Item Env:PYTHONPATH
```

## Troubleshooting

- **`py` not found:** install Python and its launcher, then reopen the terminal. If only `python` is available, use it to create the virtual environment manually.
- **Port 5000 already in use:** stop the other local app or run `python -m flask --app run:app run --port 5001` using the virtual environment's Python, then open `http://127.0.0.1:5001`.
- **Dependency installation fails:** check Internet access and repeat the setup command. Do not move an existing virtual environment between computers; recreate it on the destination.
- **Form expired:** reload the page and submit again. Signing out from another tab may invalidate an older form.
- **Can't find a record:** clear search/status filters and verify the signed-in username.
- **Forgotten password:** password reset is outside this classroom version. Create another account for a new workspace; it will not recover the old account's data.

## Implementation and limits

Python / Flask / Jinja / SQLite / SQLAlchemy / Flask-Login / Flask-WTF / custom responsive CSS. All style assets are local; normal operation does not require a CDN or external API. Installing Python packages requires Internet access. External job links naturally require Internet access.

This is a local classroom build: the launcher binds to `127.0.0.1`, debug is disabled, and it does not publish a website. Password hashing, CSRF checks, ownership checks, escaped output, and HTTP-only sessions are implemented. Public hosting, HTTPS termination, account recovery, login rate limiting, external integrations, email reminders, CSV export, and calendar view are not implemented. Do not describe it as production-deployed.

`docs/ENGINEERING.md` explains the architecture, requirements, backlog, review observations, and deviations from the proposal. `docs/DEMO_SCRIPT.md` provides a short demonstration. The initial code and automated checks were prepared with AI assistance; review and understand the source, run it yourself, and record your actual work and feedback for the course.

## Official references

- Flask application factories: https://flask.palletsprojects.com/en/stable/patterns/appfactories/
- Flask testing: https://flask.palletsprojects.com/en/stable/testing/
- Flask-WTF CSRF protection: https://flask-wtf.readthedocs.io/en/latest/csrf/
- Flask-SQLAlchemy quickstart: https://flask-sqlalchemy.palletsprojects.com/en/stable/quickstart/
- Flask-Login: https://flask-login.readthedocs.io/en/latest/
- Werkzeug password helpers: https://werkzeug.palletsprojects.com/en/stable/utils/#module-werkzeug.security
