from datetime import datetime
from ..extensions import db

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_type = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    startup_id = db.Column(db.Integer, db.ForeignKey("startups.id"), nullable=True, index=True)
    community_id = db.Column(db.Integer, nullable=True, index=True)  # reserved for later module

    author = db.relationship("User", back_populates="posts")
    startup = db.relationship("Startup", back_populates="posts")

    comments = db.relationship("Comment", back_populates="post", lazy="dynamic", cascade="all,delete")
    reactions = db.relationship("Reaction", back_populates="post", lazy="dynamic", cascade="all,delete")

class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False, index=True)

    post = db.relationship("Post", back_populates="comments")

class Reaction(db.Model):
    __tablename__ = "reactions"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # LIKE / SAVE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False, index=True)

    post = db.relationship("Post", back_populates="reactions")
