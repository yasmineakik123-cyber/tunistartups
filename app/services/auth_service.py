from flask_smorest import abort
from ..extensions import db
from ..models.user import User, UserRole
from typing import Optional

def register_user(username: str, email: str, password: str, role: str, location: Optional[str]= None ,field: Optional[str]= None, skills :Optional[str]= None):
    if role not in [r.value for r in UserRole]:
        abort(400, message="Invalid role")

    if User.query.filter_by(username=username).first():
        abort(400, message="Username already exists")

    if User.query.filter_by(email=email).first():
        abort(400, message="Email already exists")

    user = User(username=username, email=email, role=role, location=location, field=field, skills=skills)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return user

def authenticate_user(email: str, password: str):
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        abort(401, message="Invalid credentials")
    return user

