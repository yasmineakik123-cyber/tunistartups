# app/api/startup_routes.py
import secrets

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate

from ..extensions import db
from ..models.user import User
from ..models.startup import Startup, ScoreEvent

blp = Blueprint("startups", __name__, description="Startup workspace endpoints")


# =========================
# SCHEMAS
# =========================
class StartupCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    industry = fields.Str(allow_none=True)
    stage = fields.Str(allow_none=True)
    pitch = fields.Str(allow_none=True)


class StartupSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    industry = fields.Str(allow_none=True)
    stage = fields.Str(allow_none=True)
    pitch = fields.Str(allow_none=True)

    score_total = fields.Int()
    owner_id = fields.Int()
    join_code = fields.Str(allow_none=True)
    created_at = fields.Str(allow_none=True)

    # Helpful for frontend to decide owner vs member UI
    is_owner = fields.Bool(dump_only=True)


class AddMemberSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=2, max=120))


class JoinStartupSchema(Schema):
    code = fields.Str(required=True, validate=validate.Length(min=4, max=64))


class JoinCodeResponseSchema(Schema):
    join_code = fields.Str(required=True)


class ScoreEventSchema(Schema):
    id = fields.Int(dump_only=True)
    event_type = fields.Str()
    points = fields.Int()
    note = fields.Str(allow_none=True)
    created_at = fields.DateTime()
    startup_id = fields.Int()


class MemberSchema(Schema):
    id = fields.Int()
    username = fields.Str()
    role = fields.Str()


# =========================
# HELPERS
# =========================
def _current_user() -> User:
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        abort(401, message="Invalid token (user not found).")
    return user


def _require_startuper_or_admin(user: User):
    # roles: STUDENT / STARTUPER / ANGEL / ADMIN
    if user.role not in ("STARTUPER", "ADMIN"):
        abort(403, message="Only STARTUPER/ADMIN can create a startup.")


def _owned_startup(user: User):
    return Startup.query.filter_by(owner_id=user.id).order_by(Startup.id.desc()).first()


def _current_startup_id(user: User):
    owned = _owned_startup(user)
    if owned:
        return owned.id
    return user.startup_id


def _require_user_in_startup(user: User) -> int:
    sid = _current_startup_id(user)
    if not sid:
        abort(400, message="You are not linked to any startup. Join one first (join code).")
    return sid


def _is_owner_of_startup(user: User, startup_id: int) -> bool:
    return Startup.query.filter_by(id=startup_id, owner_id=user.id).first() is not None


# =========================
# SCORE ENDPOINTS
# =========================
@blp.route("/startups/score")
class StartupScore(MethodView):
    @jwt_required()
    def get(self):
        user = _current_user()
        sid = _current_startup_id(user)
        if not sid:
            return {"score_total": 0}

        s = db.session.get(Startup, sid)
        return {"score_total": s.score_total if s else 0}


@blp.route("/startups/score/events")
class StartupScoreEvents(MethodView):
    @jwt_required()
    @blp.response(200, ScoreEventSchema(many=True))
    def get(self):
        user = _current_user()
        sid = _current_startup_id(user)
        if not sid:
            return []

        events = (
            ScoreEvent.query
            .filter_by(startup_id=sid)
            .order_by(ScoreEvent.id.desc())
            .limit(50)
            .all()
        )
        return events


# =========================
# /api/startups (GET, POST)
# =========================
@blp.route("/startups")
class Startups(MethodView):
    @jwt_required()
    @blp.response(200, StartupSchema(many=True))
    def get(self):
        """
        Return the startup workspace relevant to the current user.
        - If the user owns a startup => return it
        - Else if the user is a member (startup_id set) => return that startup
        - Else => []
        """
        user = _current_user()

        owned = _owned_startup(user)
        if owned:
            data = StartupSchema().dump(owned)
            data["is_owner"] = True
            return [data]

        if user.startup_id:
            s = db.session.get(Startup, user.startup_id)
            if not s:
                return []
            data = StartupSchema().dump(s)
            data["is_owner"] = False
            return [data]

        return []

    @jwt_required()
    @blp.arguments(StartupCreateSchema)
    @blp.response(201, StartupSchema)
    def post(self, data):
        """
        Create a startup owned by the current user, and link the user to it.
        """
        user = _current_user()
        _require_startuper_or_admin(user)

        existing = Startup.query.filter_by(owner_id=user.id).first()
        if existing:
            abort(400, message="You already own a startup.")

        startup = Startup(
            name=data["name"],
            industry=data.get("industry"),
            stage=data.get("stage"),
            pitch=data.get("pitch"),
            owner_id=user.id,
        )

        db.session.add(startup)
        db.session.flush()  # ensures startup.id exists

        # link owner as member too (your logic)
        user.startup_id = startup.id

        db.session.commit()

        payload = StartupSchema().dump(startup)
        payload["is_owner"] = True
        return payload


# =========================
# /api/startups/join-code (POST)
# Owner generates/rotates join code
# =========================
@blp.route("/startups/join-code")
class StartupJoinCode(MethodView):
    @jwt_required()
    @blp.response(200, JoinCodeResponseSchema)
    def post(self):
        user = _current_user()

        startup = Startup.query.filter_by(owner_id=user.id).first()
        if not startup:
            abort(404, message="You do not own a startup.")

        code = secrets.token_hex(8)  # 16 hex chars

        startup.join_code = code
        db.session.commit()  # must persist for other users to join later

        return {"join_code": code}


# =========================
# /api/startups/join (POST)
# Member joins using join code
# =========================
@blp.route("/startups/join")
class StartupJoin(MethodView):
    @jwt_required()
    @blp.arguments(JoinStartupSchema)
    def post(self, data):
        user = _current_user()
        code = data["code"].strip()

        startup = Startup.query.filter_by(join_code=code).first()
        if not startup:
            abort(404, message="Invalid join code.")

        user.startup_id = startup.id
        db.session.commit()

        return {"message": "Joined successfully.", "startup_id": startup.id}


# =========================
# /api/startups/members (GET, POST)
# GET: list members (for dropdown in tasks assignment)
# POST: optional add member by username (still useful)
# =========================
@blp.route("/startups/members")
class StartupMembers(MethodView):
    @jwt_required()
    @blp.response(200, MemberSchema(many=True))
    def get(self):
        """
        List members of my current startup (owner or member).
        Returns minimal info for UI dropdown.
        """
        user = _current_user()
        sid = _require_user_in_startup(user)

        startup = db.session.get(Startup, sid)
        owner_id = startup.owner_id if startup else None

        members_q = User.query.filter(User.startup_id == sid)
        if owner_id:
            members_q = members_q.union(User.query.filter(User.id == owner_id))

        members = members_q.order_by(User.username.asc()).all()
        return members


    @jwt_required()
    @blp.arguments(AddMemberSchema)
    def post(self, data):
        """
        Optional: Owner can add a user to their startup by username.
        """
        owner = _current_user()
        my_startup = Startup.query.filter_by(owner_id=owner.id).first()
        if not my_startup:
            abort(400, message="You don't own a startup yet. Create one first.")

        username = data["username"].strip()
        target = User.query.filter_by(username=username).first()
        if not target:
            abort(404, message="User not found.")

        if target.startup_id == my_startup.id:
            return {"message": f"{target.username} is already in your startup."}, 200

        target.startup_id = my_startup.id
        db.session.commit()
        return {"message": f"Added {target.username} to startup '{my_startup.name}'."}, 200
