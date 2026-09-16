# Digital Legacy Vault & Inheritance Management System

A college/final-year prototype for securely organizing and managing information
about a person's assets, nominees, documents, will, and digital accounts, with
a simulated life-verification and family-release workflow.

**Status: Step 1 (Project Setup) and Step 2 (Registration / Login / Logout)
are implemented.** All other modules (Assets, Nominees, Will, AI Checker,
Documents, Digital Legacy, Trusted Contact, Life Verification, Tasks) exist
as empty placeholder files and will be built in later steps.

## Tech Stack
- Backend: Python, Flask
- Database: SQLite + SQLAlchemy
- Frontend: HTML, Bootstrap 5
- Security: Werkzeug password hashing, Flask sessions, `cryptography` (for later steps)

## Installation

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
cp .env.example .env       # then edit .env with your own SECRET_KEY
python app.py
```

Visit **http://127.0.0.1:5000** in your browser.

## What works right now
- Register a new Vault Owner account (password is hashed, never stored in plain text)
- Login with email/password
- Basic login-attempt protection (account locks for 15 minutes after 5 failed attempts)
- Session-based authentication with `login_required` protection on the dashboard
- Logout
- Every login/logout/registration event is written to the `audit_logs` table
- Placeholder dashboard showing zeroed stat cards for future modules

## Project Structure
```
digital-legacy-vault/
├── app.py                 # Application factory + entry point
├── config.py               # Configuration (reads from .env)
├── extensions.py           # Shared SQLAlchemy db instance
├── models/                 # SQLAlchemy models (user, audit done; rest are stubs)
├── routes/                 # Flask blueprints (auth, dashboard done; rest are stubs)
├── services/                # audit_service done; rest are stubs
├── templates/               # Jinja2 templates (base/login/register/dashboard done)
├── static/css, static/js
├── database/                # legacy_vault.db created here at runtime
└── uploads/                 # future document storage (outside static/)
```

## Security notes (Step 1–2)
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Generic "Email or password is incorrect" message (no user enumeration)
- Session cookies are HttpOnly, SameSite=Lax, and Secure in production
- Session expires after 30 minutes of inactivity
- No stack traces shown to users (custom error handlers)

## Legal Disclaimer
This application is an information-management and workflow prototype. It does
not replace a legally valid will, legal advice, executor, court process,
financial institution process, or applicable government procedure.

## Next Steps
See the project plan — Steps 3 through 15 will add the dashboard stats,
asset/nominee/document/will management, the rule-based AI checker, digital
legacy, trusted contacts, life verification, family dashboard, and inheritance
tasks.
