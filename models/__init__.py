"""
Import every model here so that a single `from models import *` (or the
import of this package in app.py) registers all tables with SQLAlchemy
before db.create_all() runs.

Steps 3+ will add: asset, nominee, document, will, digital_asset,
trusted_contact, verification, task.
"""
from models.user import User
from models.audit import AuditLog

__all__ = ["User", "AuditLog"]
