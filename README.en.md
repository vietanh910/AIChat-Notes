# AIChat-Notes (Flask + SQLite)

A simple note-taking app built with Flask, storing note content as files and metadata in SQLite. It supports folders, pinning, sorting, searching, sharing via code, image uploads, and AI Q&A (Gemini). Email reminders are powered by APScheduler + SMTP.

---

## 1) Features
- Accounts: register/login/logout
- Manage folders and notes; pin folders/notes; sort by name/date; search folders
- Note content is saved to `.md` files inside `notes/`
- Upload images to `notes/images/` and insert into notes
- Share a note via code and import by share code
- Ask AI questions about the note using Google Gemini (if API key is provided)
- Email reminders via APScheduler
- UI languages: Vietnamese / English (toggle in UI)

## 2) Requirements
- Windows with Python 3.10+ (3.12 recommended)
- Optional: Docker Desktop (to run with Docker)
- Optional: Google Gemini API Key (enable AI) and an SMTP account (send reminder emails)

## 3) Quick start (Windows - cmd.exe)

1. Create and activate a virtual environment
```bat
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies
```bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Create a `.env` file (same folder as `app.py`)
```ini
# .env
FLASK_SECRET_KEY=change-me-please
# Enable AI Q&A if you have a Gemini key
GEMINI_API_KEY=your-gemini-api-key
# (optional) override model if needed
GEMINI_MODEL=gemini-2.0-flash-exp
```

4. Configure email (optional, for reminder emails)
- Open `app.py`, find the mail config and update these two lines to your SMTP account:
  - `app.config['MAIL_USERNAME'] = 'your-email@example.com'`
  - `app.config['MAIL_PASSWORD'] = 'your-app-password-or-smtp-password'`
- For Gmail, use an App Password (not your normal password). Default server is `smtp.gmail.com:587` and `MAIL_USE_TLS=True`.

5. Run the app
```bat
python app.py
```
- Open: http://127.0.0.1:5000
- On first run it creates `notes.db` and required folders. A demo account `demo/demo` is available, or register a new one.

## 4) Quick usage
- Create folders and notes; click a note to open the editor
- Use the image button to upload images (stored in `notes/images/`)
- Pin folders/notes to keep them on top; sort by name/date; search folders
- Share: generate a share code from a note and import it on another account
- AI chat: enabled when `GEMINI_API_KEY` is set (answers questions about the note content)
- Reminders: set an email and a future time; APScheduler will send the email

## 5) Project structure
- `app.py` — Flask app entry, routes, DB, upload, sharing, chat, reminders
- `gemini_service.py` — Google Gemini integration; reads `GEMINI_API_KEY` from `.env`
- `notes.db` — SQLite database
- `notes/` — note content files (user-scoped filenames)
  - `notes/images/` — uploaded images
- `templates/` — Jinja2 HTML templates
- `static/` — CSS/JS and static assets
- `scripts/clear_notes_db.py` — script to wipe data while preserving schema

## 6) Working with the database (SQLite)

Open the database:
- Use DB Browser for SQLite (GUI) and open `notes.db`, or
- Install `sqlite3` CLI (optional on Windows) and run:
```bat
sqlite3 notes.db
.tables
.schema
.exit
```

Delete data but keep tables (preserve schema):
- Option 1: use the provided script
```bat
.venv\Scripts\activate
python scripts\clear_notes_db.py
```
- Option 2: do it manually in SQLite (example: wipe notes/folders/shares only)
```sql
DELETE FROM shared_notes;
DELETE FROM notes;
DELETE FROM folders;
-- optional: remove custom users but keep demo
-- DELETE FROM users WHERE username <> 'demo';
VACUUM;
```

Delete note content files (not images):
```bat
DEL /Q notes\*.md
```

Note: Stop the app before touching the DB file to avoid locks.

## 7) Run with Docker
Requires Docker Desktop on Windows.

1. Build the image
```bat
docker build -t aichat-notes .
```

2. Create a `.env` as above (at least `FLASK_SECRET_KEY`, optionally `GEMINI_API_KEY`).

3. Run the container (simple mode, no mounts — data lives in the container)
```bat
docker run --name aichat-notes -p 5000:5000 --env-file .env aichat-notes
```

4. Recommended: run with volume mounts to persist data outside the container
```bat
docker run --name aichat-notes -p 5000:5000 --env-file .env ^
  -v "%cd%\notes":/app/notes ^
  -v "%cd%\notes.db":/app/notes.db ^
  aichat-notes
```
- Open: http://localhost:5000

Notes:
- The `Dockerfile` exposes port 5000 and runs `flask run` in production env. Port mapping `-p 5000:5000` is enough to reach it from your host.
- If you mount only `notes/` but not `notes.db`, the DB will remain inside the container (it will be lost when the container is removed).

## 8) Security and configuration
- Set a strong `FLASK_SECRET_KEY` in `.env`
- Do not commit `GEMINI_API_KEY` or SMTP passwords to the repo
- For Gmail SMTP: enable 2FA + use an App Password; keep `MAIL_USE_TLS=True` and port 587
- By default `app.py` runs on `host=127.0.0.1` (local only). To access from another machine, change to `app.run(host="0.0.0.0", ...)` or run via Docker and publish the port

## 9) Troubleshooting
- Dependencies fail to install: upgrade pip and verify Python version
```bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```
- Port in use: change the port or stop the process using 5000
- Gemini not responding: check `GEMINI_API_KEY` in `.env` and your network
- Email send errors: verify SMTP, username/password (App Password), firewall, and that the reminder time is in the future
- Image upload errors: check image type/size and that `notes/images/` is writable

## 10) License
See `LICENSE-CODE`. Remove/ignore secrets (`.env`, passwords) before sharing your code.

