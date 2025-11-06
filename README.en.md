# AIChat-Notes (Flask + SQLite)

A simple note-taking app built with Flask, storing note content as files and metadata in SQLite. It supports folders, pinning, sorting, searching, sharing via code, image uploads, and AI Q&A (Gemini). Email reminders are powered by APScheduler + SMTP.

---

## 1) Features
- Accounts: register/login/logout
- Manage folders and notes; pin folders/notes; sort by name/date; search folders
- Format, edit notes
- Note content is saved to `notes.db`
- Share a note via code and import by share code
- Ask AI questions about the note using Google Gemini (if API key is provided)
- Email reminders via APScheduler
- UI languages: Vietnamese / English (toggle in UI)
- UI Dark/Light

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

3. Add API key to use chatbot
```
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
- Use the image button to upload images
- Pin folders/notes to keep them on top; sort by name/date; search folders
- Share: generate a share code from a note and import it on another account
- AI chat: enabled when `GEMINI_API_KEY` is set
- Reminders: set an email and a future time; APScheduler will send the email

## 5) Run with Docker
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


## 6) License
See `LICENSE-CODE`. Remove/ignore secrets (`.env`, passwords, API key) before sharing your code.

