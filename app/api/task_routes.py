

# app/api/task_routes.py
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate

from ..extensions import db
from ..models.user import User
from ..models.task import Task
from ..models.startup import Startup
from ..services.score_service import add_score_event

blp = Blueprint("tasks", __name__, description="Tasks endpoints")


# ----------------
# Schemas
# ----------------
class TaskCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    description = fields.Str(allow_none=True)
    priority = fields.Str(
        validate=validate.OneOf(["LOW", "MEDIUM", "HIGH"]),
        load_default="MEDIUM",
    )
    due_date = fields.Date(allow_none=True)
    assignee_username = fields.Str(allow_none=True)  # assign by username


class TaskUpdateSchema(Schema):
    title = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    status = fields.Str(allow_none=True, validate=validate.OneOf(["TODO", "IN_PROGRESS", "DONE"]))
    priority = fields.Str(allow_none=True, validate=validate.OneOf(["LOW", "MEDIUM", "HIGH"]))
    due_date = fields.Date(allow_none=True)
    assignee_username = fields.Str(allow_none=True)


class TaskSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str()
    description = fields.Str(allow_none=True)
    status = fields.Str()
    priority = fields.Str()
    due_date = fields.Date(allow_none=True)
    created_at = fields.DateTime()

    startup_id = fields.Int()
    created_by_id = fields.Int()
    assigned_to_id = fields.Int(allow_none=True)

    assignee_username = fields.Method("get_assignee_username")
    creator_username = fields.Method("get_creator_username")

    def get_assignee_username(self, obj):
        return obj.assigned_to.username if obj.assigned_to else None

    def get_creator_username(self, obj):
        return obj.created_by.username if obj.created_by else None


# ----------------
# Helpers
# ----------------
def _current_user() -> User:
    uid = get_jwt_identity()
    user = db.session.get(User, uid)
    if not user:
        abort(401, message="Invalid token.")
    return user


def _owned_startup(user: User):
    return Startup.query.filter_by(owner_id=user.id).first()


def _require_user_in_startup(user: User) -> int:
    """
    User must be:
    - owner of a startup, OR
    - member of a startup (startup_id set)
    """
    owned = _owned_startup(user)
    if owned:
        return owned.id
    if user.startup_id:
        return user.startup_id
    abort(400, message="You are not linked to any startup. Join one first (join code).")


def _is_owner(user: User, startup_id: int) -> bool:
    return Startup.query.filter_by(id=startup_id, owner_id=user.id).first() is not None


def _is_owner_or_admin(user: User, startup_id: int) -> bool:
    return user.role == "ADMIN" or _is_owner(user, startup_id)


def _require_owner_or_admin(user: User, startup_id: int):
    if not _is_owner_or_admin(user, startup_id):
        abort(403, message="Only the startup owner (or ADMIN) can create/assign tasks.")


def _require_task_in_same_startup(task: Task, startup_id: int):
    if not task or task.startup_id != startup_id:
        abort(404, message="Task not found.")


def _require_target_in_same_startup(target: User, startup_id: int):
    """
    target is valid if:
    - target.startup_id == startup_id  (member)
    OR
    - target owns that startup (edge case)
    """
    if target.startup_id == startup_id:
        return
    owned = _owned_startup(target)
    if owned and owned.id == startup_id:
        return
    abort(400, message="This user is not a member of your startup.")


# ----------------
# Routes
# ----------------
@blp.route("/tasks")
class Tasks(MethodView):

    @jwt_required()
    @blp.response(200, TaskSchema(many=True))
    def get(self):
        """
        OPTION 2 behavior:
        - Owner/Admin: sees ALL tasks in the startup
        - Member: sees ONLY tasks assigned to them
        """
        user = _current_user()
        startup_id = _require_user_in_startup(user)

        q = Task.query.filter(Task.startup_id == startup_id)

        if not _is_owner_or_admin(user, startup_id):
            q = q.filter(Task.assigned_to_id == user.id)

        return q.order_by(Task.id.desc()).all()

    @jwt_required()
    @blp.arguments(TaskCreateSchema)
    @blp.response(201, TaskSchema)
    def post(self, data):
        """
        Owner/Admin creates a task in the startup and can assign by username.
        """
        user = _current_user()
        startup_id = _require_user_in_startup(user)
        _require_owner_or_admin(user, startup_id)

        assigned_to_id = None
        uname = (data.get("assignee_username") or "").strip()
        if uname:
            target = User.query.filter_by(username=uname).first()
            if not target:
                abort(404, message="Assignee username not found.")
            _require_target_in_same_startup(target, startup_id)
            assigned_to_id = target.id

        task = Task(
            title=data["title"],
            description=data.get("description"),
            priority=data.get("priority", "MEDIUM"),
            status="TODO",
            due_date=data.get("due_date"),
            startup_id=startup_id,
            created_by_id=user.id,
            assigned_to_id=assigned_to_id,
        )

        db.session.add(task)
        db.session.commit()
        return task


@blp.route("/tasks/<int:task_id>")
class TaskItem(MethodView):

    @jwt_required()
    @blp.response(200, TaskSchema)
    def get(self, task_id):
        user = _current_user()
        startup_id = _require_user_in_startup(user)

        task = db.session.get(Task, task_id)
        _require_task_in_same_startup(task, startup_id)

        # Members can only view their assigned tasks
        if not _is_owner_or_admin(user, startup_id):
            if task.assigned_to_id != user.id:
                abort(403, message="You can only view tasks assigned to you.")

        return task

    @jwt_required()
    @blp.arguments(TaskUpdateSchema)
    @blp.response(200, TaskSchema)
    def patch(self, data, task_id):
        user = _current_user()
        startup_id = _require_user_in_startup(user)

        task = db.session.get(Task, task_id)
        _require_task_in_same_startup(task, startup_id)

        owner_like = _is_owner_or_admin(user, startup_id)

        # Members: only update status of tasks assigned to them
        if not owner_like:
            if task.assigned_to_id != user.id:
                abort(403, message="You can only update tasks assigned to you.")

            # Only allow "status"
            for k, v in data.items():
                if k != "status" and v is not None:
                    abort(403, message="Members can only update task status.")

        old_status = task.status

        # Owner/Admin can update all editable fields
        if owner_like:
            if data.get("title") is not None:
                task.title = data["title"]
            if data.get("description") is not None:
                task.description = data["description"]
            if data.get("priority") is not None:
                task.priority = data["priority"]
            if data.get("due_date") is not None:
                task.due_date = data["due_date"]

            # Owner/Admin can re-assign by username
            if data.get("assignee_username") is not None:
                uname = (data.get("assignee_username") or "").strip()
                if uname == "":
                    task.assigned_to_id = None
                else:
                    target = User.query.filter_by(username=uname).first()
                    if not target:
                        abort(404, message="Assignee username not found.")
                    _require_target_in_same_startup(target, startup_id)
                    task.assigned_to_id = target.id

        # Everyone (owner/admin/member assigned) can update status, but members only have this
        if data.get("status") is not None:
            task.status = data["status"]

        db.session.commit()

        # Score trigger (after commit OK, but depends only on status transition)
        if old_status != "DONE" and task.status == "DONE":
            add_score_event(
                startup_id,
                "TASK_DONE",
                3,
                note=f"Task completed: {task.title}",
            )

        return task

    @jwt_required()
    def delete(self, task_id):
        user = _current_user()
        startup_id = _require_user_in_startup(user)
        _require_owner_or_admin(user, startup_id)

        task = db.session.get(Task, task_id)
        _require_task_in_same_startup(task, startup_id)

        db.session.delete(task)
        db.session.commit()
        return {"message": "Task deleted."}, 200