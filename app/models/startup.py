from datetime import datetime
from ..extensions import db


class Startup(db.Model):
    __tablename__ = "startups"  # MUST be 'startups'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(120), nullable=True)
    stage = db.Column(db.String(120), nullable=True)
    pitch = db.Column(db.Text, nullable=True)

    score_total = db.Column(db.Integer, nullable=False, default=0)

    join_code = db.Column(db.String(32), unique=True, nullable=True, index=True)

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), create_constraint=False , nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship(
        "User",
        back_populates="owned_startups",
        foreign_keys=[owner_id],
    )

    posts = db.relationship("Post", back_populates="startup", lazy="dynamic")
    score_events = db.relationship("ScoreEvent", back_populates="startup", lazy="dynamic")


class ScoreEvent(db.Model):
    __tablename__ = "score_events"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(80), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    startup_id = db.Column(db.Integer, db.ForeignKey("startups.id"), nullable=False, index=True)
    startup = db.relationship("Startup", back_populates="score_events")