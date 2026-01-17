from datetime import datetime
from enum import Enum

from passlib.hash import bcrypt
from ..extensions import db


class UserRole(str, Enum):
    STUDENT = "STUDENT"
    STARTUPER = "STARTUPER"
    ANGEL = "ANGEL"
    ADMIN = "ADMIN"


class User(db.Model):
    __tablename__ = "users"  # MUST be 'users'

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default=UserRole.STUDENT.value)
    location = db.Column(db.String(120), nullable=True)

    # membership to a startup (optional)
    startup_id = db.Column(db.Integer, db.ForeignKey("startups.id"), create_constraint=False , nullable=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    field = db.Column(db.String(80), nullable=True)      # ex: "Data Analytics"
    skills = db.Column(db.String(255), nullable=True)    # ex: "Python, Power BI"
    
    # relationships
    owned_startups = db.relationship(
        "Startup",
        back_populates="owner",
        foreign_keys="Startup.owner_id",
        lazy="dynamic",
    )

    posts = db.relationship("Post", back_populates="author", lazy="dynamic")
    notifications = db.relationship("Notification", back_populates="user", lazy="dynamic")

    def set_password(self, raw_password: str):
        self.password_hash = bcrypt.hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.verify(raw_password, self.password_hash)
