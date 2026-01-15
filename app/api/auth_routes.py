from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from ..models.user import User
from ..services.auth_service import register_user, authenticate_user
from ..schemas import RegisterSchema, LoginSchema, TokenSchema, MeSchema

blp = Blueprint("Auth", "auth", description="Auth endpoints")

def make_token(user: User):
    additional_claims = {
        "role": user.role,
        "startup_id": user.startup_id
    }
    return create_access_token(identity=str(user.id), additional_claims=additional_claims)

@blp.route("/auth/register")
class Register(MethodView):
    @blp.arguments(RegisterSchema)
    @blp.response(201, TokenSchema)
    def post(self, data):
        user = register_user(
            username=data["username"],
            password=data["password"],
            role=data["role"],
            location=data.get("location"),
            field=data.get("field"),
            skills=data.get("skills")
            
        )
        return {"access_token": make_token(user)}

@blp.route("/auth/login")
class Login(MethodView):
    @blp.arguments(LoginSchema)
    @blp.response(200, TokenSchema)
    def post(self, data):
        user = authenticate_user(data["username"], data["password"])
        return {"access_token": make_token(user)}

@blp.route("/users/me")
class Me(MethodView):
    @jwt_required()
    @blp.response(200, RegisterSchema)
    def get(self):
        user_id = int(get_jwt_identity())
        user = User.query.get_or_404(user_id)
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "location": user.location,
            "startup_id": user.startup_id,
            "field": user.field,
            "skills": user.skills
            
        }
