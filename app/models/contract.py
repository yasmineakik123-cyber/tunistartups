from datetime import datetime
from sqlalchemy import Enum
from ..extensions import db


class Contract(db.Model):
    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    template_type = db.Column(db.String(80), nullable=False)

    # generated contract body (simulation text)
    content = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT",  # DRAFT / SENT / SIGNED / CANCELLED
        index=True,
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    signatures = db.relationship(
        "Signature",
        backref="contract",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
