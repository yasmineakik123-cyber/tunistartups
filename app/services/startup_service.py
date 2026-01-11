from flask_smorest import abort
from ..extensions import db
from ..models.startup import Startup
from ..models.user import UserRole

def create_startup_for_owner(owner, payload: dict):
    if owner.role not in [UserRole.STARTUPER.value, UserRole.ADMIN.value]:
        abort(403, message="Only STARTUPER/ADMIN can create startups")

    if owner.startup_id is not None:
        abort(400, message="User already linked to a startup workspace")

    startup = Startup(
        name=payload["name"],
        industry=payload.get("industry"),
        stage=payload.get("stage"),
        pitch=payload.get("pitch"),
        owner_id=owner.id,
    )
    db.session.add(startup)
    db.session.flush()

    owner.startup_id = startup.id
    db.session.add(owner)
    db.session.commit()

    return startup