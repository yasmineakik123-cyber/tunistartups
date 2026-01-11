from datetime import datetime
from ..extensions import db


class Signature(db.Model):
    __tablename__ = "signatures"

    id = db.Column(db.Integer, primary_key=True)

    contract_id = db.Column(db.Integer, db.ForeignKey("contracts.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING",  # PENDING / SIGNED / REJECTED
        index=True,
    )

    signed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("contract_id", "user_id", name="uq_signature_contract_user"),
    )