"""
Central place for extension objects (SQLAlchemy, etc.).

Keeping this separate from app.py avoids circular imports: models need
`db`, and app.py needs the models registered with `db`, so both sides
import from here instead of from each other.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
