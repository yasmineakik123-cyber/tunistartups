from flask_smorest import abort
from ..extensions import db
from ..models.user import User, UserRole
from typing import Optional

def register_user(username: str, password: str, role: str, location: Optional[str]= None ,field: Optional[str]= None, skills :Optional[str]= None):
    if role not in [r.value for r in UserRole]:
        abort(400, message="Invalid role")

    if User.query.filter_by(username=username).first():
        abort(400, message="Username already exists")

    user = User(username=username, role=role, location=location, field=field, skills=skills)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return user

def authenticate_user(username: str, password: str):
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        abort(401, message="Invalid credentials")
    return user

