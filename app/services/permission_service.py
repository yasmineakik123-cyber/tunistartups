from flask_jwt_extended import get_jwt
from flask_smorest import abort

def require_roles(*allowed_roles: str):
    claims = get_jwt()
    role = claims.get("role")
    if role not in allowed_roles:
        abort(403, message="Forbidden: insufficient role")

def require_startup_workspace():
    claims = get_jwt()
    startup_id = claims.get("startup_id")
    if not startup_id:
        abort(403, message="No startup workspace linked to this user")
    return startup_id
