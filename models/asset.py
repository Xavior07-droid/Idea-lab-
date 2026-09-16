from datetime import datetime
from extensions import db


class Asset(db.Model):
    """
    An asset belonging to a vault owner (property, bank account, insurance,
    vehicle, investment, etc).
    """

    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    provider = db.Column(db.String(150), nullable=True)
    reference = db.Column(db.String(150), nullable=True)
    approx_value = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Asset id={self.id} name={self.name}>"
