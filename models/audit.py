from datetime import datetime
from extensions import db


class AuditLog(db.Model):
    """
    Records security-relevant events.

    NEVER log passwords, encryption keys, tokens, or full document contents
    here — only metadata about what happened.
    """

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    action = db.Column(db.String(80), nullable=False)
    # e.g. login_success, login_failed, logout, register

    resource = db.Column(db.String(120), nullable=True)
    result = db.Column(db.String(20), nullable=False, default="success")
    # success | failure

    ip_address = db.Column(db.String(64), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} user={self.user_id} result={self.result}>"
