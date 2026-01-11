from ..extensions import db
from ..models.task import Task
from ..models.user import User
from ..models.startup import Startup


# -------------------------
# Startup helpers (owner or member)
# -------------------------
def _startup_id_for_user(user):
    """
    Returns the startup_id for:
    - owner (Startup.owner_id == user.id)
    - member (user.startup_id)
    """
    owned = Startup.query.filter_by(owner_id=user.id).first()
    if owned:
        return owned.id
    if user.startup_id:
        return user.startup_id
    raise ValueError("You are not linked to any startup workspace.")


def _is_owner_or_admin(user, startup_id):
    if user.role == "ADMIN":
        return True
    owned = Startup.query.filter_by(id=startup_id, owner_id=user.id).first()
    return owned is not None


def _require_owner_or_admin(user, startup_id):
    if not _is_owner_or_admin(user, startup_id):
        raise ValueError("Only the startup owner (or ADMIN) can create/assign tasks.")


def _validate_assignee_same_startup(startup_id, assignee_username):
    """
    Returns assignee_id or None.
    Assignee must be a member of the same startup (or the owner of that startup).
    """
    if not assignee_username:
        return None

    uname = assignee_username.strip()
    if uname == "":
        return None

    target = User.query.filter_by(username=uname).first()
    if not target:
        raise ValueError("Assignee username not found.")

    # Member case
    if target.startup_id == startup_id:
        return target.id

    # Owner case (edge case, but allow it)
    owned = Startup.query.filter_by(id=startup_id, owner_id=target.id).first()
    if owned:
        return target.id

    raise ValueError("This user is not a member of your startup.")


# -------------------------
# CRUD
# -------------------------
def list_tasks_for_user(user):
    """
    OPTION 2:
    - Owner/Admin: sees ALL tasks in the startup
    - Member: sees ONLY tasks assigned to them
    """
    startup_id = _startup_id_for_user(user)

    q = Task.query.filter_by(startup_id=startup_id)

    if not _is_owner_or_admin(user, startup_id):
        q = q.filter(Task.assigned_to_id == user.id)

    return q.order_by(Task.created_at.desc()).all()


def create_task(user, data):
    """
    Owner/Admin only.
    Assign by assignee_username (optional).
    """
    startup_id = _startup_id_for_user(user)
    _require_owner_or_admin(user, startup_id)

    assigned_to_id = _validate_assignee_same_startup(
        startup_id,
        data.get("assignee_username"),
    )

    task = Task(
        title=data["title"],
        description=data.get("description"),
        priority=data.get("priority") or "MEDIUM",
        due_date=data.get("due_date"),
        status="TODO",
        startup_id=startup_id,
        created_by_id=user.id,
        assigned_to_id=assigned_to_id,
    )

    db.session.add(task)
    db.session.commit()
    return task


def update_task(user, task_id, data):
    """
    OPTION 2:
    - Owner/Admin can update anything + reassign
    - Member can only update status AND only if assigned to them
    """
    startup_id = _startup_id_for_user(user)

    task = Task.query.get(task_id)
    if not task:
        raise ValueError("Task not found.")

    if task.startup_id != startup_id:
        raise ValueError("Not allowed.")

    owner_like = _is_owner_or_admin(user, startup_id)

    # Member restrictions
    if not owner_like:
        if task.assigned_to_id != user.id:
            raise ValueError("You can only update tasks assigned to you.")

        # only status is allowed
        for k, v in data.items():
            if k != "status" and v is not None:
                raise ValueError("Members can only update task status.")

    # save old status for transition logic
    old_status = task.status

    # Owner/Admin edits
    if owner_like:
        if "title" in data and data["title"] is not None:
            task.title = data["title"]
        if "description" in data:
            task.description = data.get("description")

        if "priority" in data and data["priority"] is not None:
            task.priority = data["priority"]
        if "due_date" in data:
            task.due_date = data.get("due_date")

        # reassign by username
        if "assignee_username" in data:
            task.assigned_to_id = _validate_assignee_same_startup(
                startup_id,
                data.get("assignee_username"),
            )

    # Everyone allowed (but for member this is the only thing)
    if "status" in data and data["status"] is not None:
        task.status = data["status"]

    db.session.commit()

    # NOTE: scoring can be handled in routes or here; this file currently does not import score_service
    # If you want, we can add "if old_status != DONE and task.status == DONE: add_score_event(...)"

    return task


def delete_task(user, task_id):
    """
    Owner/Admin only.
    """
    startup_id = _startup_id_for_user(user)
    _require_owner_or_admin(user, startup_id)

    task = Task.query.get(task_id)
    if not task:
        raise ValueError("Task not found.")

    if task.startup_id != startup_id:
        raise ValueError("Not allowed.")

    db.session.delete(task)
    db.session.commit()
    return True