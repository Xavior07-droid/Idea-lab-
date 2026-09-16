from flask import request
from extensions import db
from models.audit import AuditLog


def log_event(action: str, user_id: int | None = None, resource: str | None = None,
              result: str = "success") -> None:
    """
    Write one row to the audit_logs table.

    Called from routes after security-relevant events (login, logout,
    registration, etc). Never pass passwords or secrets as `resource`.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        result=result,
        ip_address=request.remote_addr if request else None,
    )
    db.session.add(entry)
    db.session.commit()
