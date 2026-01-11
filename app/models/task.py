from datetime import datetime
from ..extensions import db

class TaskStatus:
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"

class TaskPriority:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), nullable=False, default=TaskStatus.TODO)
    priority = db.Column(db.String(20), nullable=False, default=TaskPriority.MEDIUM)

    due_date = db.Column(db.Date, nullable=True)

    # Tenant isolation
    startup_id = db.Column(db.Integer, db.ForeignKey("startups.id"), nullable=False, index=True)

    # Who created it
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Who it is assigned to
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    startup = db.relationship("Startup", foreign_keys=[startup_id])
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id])
