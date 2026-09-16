from datetime import datetime
from extensions import db


# Many-to-many link between assets and nominees ("assign nominee to asset").
asset_nominees = db.Table(
    "asset_nominees",
    db.Column("asset_id", db.Integer, db.ForeignKey("assets.id"), primary_key=True),
    db.Column("nominee_id", db.Integer, db.ForeignKey("nominees.id"), primary_key=True),
)


class Nominee(db.Model):
    """
    A person a vault owner names to receive/manage one or more assets.
    """

    __tablename__ = "nominees"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    name = db.Column(db.String(150), nullable=False)
    relationship = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(30), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    assets = db.relationship(
        "Asset",
        secondary=asset_nominees,
        backref=db.backref("nominees", lazy="dynamic"),
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Nominee id={self.id} name={self.name}>"
