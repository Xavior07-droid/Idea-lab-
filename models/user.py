from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    """
    Vault Owner account.

    Passwords are NEVER stored in plain text — only a salted hash produced
    by werkzeug.security.generate_password_hash() is kept.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default="vault_owner")
    # roles: vault_owner, administrator

    # Basic login-attempt protection (Step 2 security requirement).
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)

    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # --- Password helpers -------------------------------------------------
    def set_password(self, plain_password: str) -> None:
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        return check_password_hash(self.password_hash, plain_password)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
