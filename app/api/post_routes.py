from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import or_

from ..extensions import db
from ..models.post import Post, Comment, Reaction
from ..models.notification import Notification
from ..schemas import PostCreateSchema, PostSchema, CommentCreateSchema, ReactionCreateSchema

blp = Blueprint("Posts", "posts", description="Posts endpoints")

def notify(user_id: int, message: str, kind: str = None, related_post_id: int = None):
    n = Notification(user_id=user_id, message=message, kind=kind, related_post_id=related_post_id)
    db.session.add(n)

@blp.route("/posts")
class Posts(MethodView):
    @jwt_required()
    @blp.arguments(PostCreateSchema)
    @blp.response(201, PostSchema)
    def post(self, payload):
        claims = get_jwt()
        role = claims.get("role")
        my_startup_id = claims.get("startup_id")
        author_id = int(get_jwt_identity())

        if role not in ["STARTUPER", "ANGEL", "ADMIN"]:
            abort(403, message="Only STARTUPER/ANGEL can post")

        target_startup_id = payload.get("startup_id")
        if target_startup_id is not None:
            if role != "ADMIN" and my_startup_id != target_startup_id:
                abort(403, message="Forbidden: cannot post into another startup workspace")

        post = Post(
            title=payload["title"],
            content=payload["content"],
            post_type=payload.get("post_type"),
            author_id=author_id,
            startup_id=payload.get("startup_id"),
            community_id=payload.get("community_id"),
        )
        db.session.add(post)
        db.session.commit()
        return post

    @jwt_required()
    @blp.response(200, PostSchema(many=True))
    def get(self):
        claims = get_jwt()
        my_startup_id = claims.get("startup_id")

        q = Post.query
        if my_startup_id:
            q = q.filter(or_(Post.startup_id == my_startup_id, Post.startup_id.is_(None)))
        else:
            q = q.filter(Post.startup_id.is_(None))

        return q.order_by(Post.id.desc()).all()

@blp.route("/posts/<int:post_id>/comments")
class PostComments(MethodView):
    @jwt_required()
    @blp.arguments(CommentCreateSchema)
    def post(self, payload, post_id):
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        my_startup_id = claims.get("startup_id")

        post = Post.query.get_or_404(post_id)

        if post.startup_id is not None and post.startup_id != my_startup_id and claims.get("role") != "ADMIN":
            abort(403, message="Forbidden: not your workspace")

        comment = Comment(content=payload["content"], author_id=user_id, post_id=post_id)
        db.session.add(comment)

        if post.author_id != user_id:
            notify(post.author_id, "New comment on your post", kind="COMMENT", related_post_id=post_id)

        db.session.commit()
        return {"message": "Comment added"}, 201

@blp.route("/posts/<int:post_id>/reactions")
class PostReactions(MethodView):
    @jwt_required()
    @blp.arguments(ReactionCreateSchema)
    def post(self, payload, post_id):
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        my_startup_id = claims.get("startup_id")

        post = Post.query.get_or_404(post_id)

        if post.startup_id is not None and post.startup_id != my_startup_id and claims.get("role") != "ADMIN":
            abort(403, message="Forbidden: not your workspace")

        existing = Reaction.query.filter_by(user_id=user_id, post_id=post_id, type=payload["type"]).first()
        if existing:
            return {"message": "Already reacted"}, 200

        r = Reaction(type=payload["type"], user_id=user_id, post_id=post_id)
        db.session.add(r)

        if post.author_id != user_id:
            notify(post.author_id, f"New reaction: {payload['type']}", kind="REACTION", related_post_id=post_id)

        db.session.commit()
        return {"message": "Reaction added"}, 201
