from datetime import datetime
from ..extensions import db


class Bank(db.Model):
    __tablename__ = "banks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    loan_rates = db.relationship(
        "LoanRate",
        back_populates="bank",
        lazy="dynamic",
        cascade="all,delete",
    )


class LoanRate(db.Model):
    __tablename__ = "loan_rates"

    id = db.Column(db.Integer, primary_key=True)

    bank_id = db.Column(db.Integer, db.ForeignKey("banks.id"), nullable=False, index=True)
    product_name = db.Column(db.String(200), nullable=False)
    rate_value = db.Column(db.Float, nullable=False)

    valid_from = db.Column(db.Date, nullable=True)
    valid_to = db.Column(db.Date, nullable=True)

    source_note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bank = db.relationship("Bank", back_populates="loan_rates")


class LegalResource(db.Model):
    __tablename__ = "legal_resources"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(240), nullable=False)
    category = db.Column(db.String(120), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
