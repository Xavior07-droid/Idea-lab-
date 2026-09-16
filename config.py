import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Secret key used to sign session cookies. In production this MUST come
    # from an environment variable and never be hard-coded.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # SQLite database stored inside the database/ folder.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database', 'legacy_vault.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploaded documents are stored outside the "static" folder so they are
    # never served directly by Flask's static file handler.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max upload size
    ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}

    # Session / cookie security settings.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # SESSION_COOKIE_SECURE should be True in production (requires HTTPS).
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # Key used by the encryption service (services/encryption.py) for
    # sensitive fields. Generated with Fernet.generate_key() and stored in
    # .env — never commit a real key to source control.
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")

    # Basic login-attempt protection.
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 15
