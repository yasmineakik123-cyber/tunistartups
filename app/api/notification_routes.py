from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models.notification import Notification
from ..extensions import db
from ..schemas import NotificationSchema

blp = Blueprint("Notifications", "notifications", description="Notification endpoints")

@blp.route("/notifications")
class Notifications(MethodView):
    @jwt_required()
    @blp.response(200, NotificationSchema(many=True))
    def get(self):
        user_id = int(get_jwt_identity())
        return Notification.query.filter_by(user_id=user_id).order_by(Notification.id.desc()).all()

@blp.route("/notifications/<int:notif_id>/read")
class NotificationRead(MethodView):
    @jwt_required()
    def patch(self, notif_id):
        user_id = int(get_jwt_identity())
        n = Notification.query.get_or_404(notif_id)
        if n.user_id != user_id:
            return {"message": "Forbidden"}, 403
        n.is_read = True
        db.session.add(n)
        db.session.commit()
        return {"message": "Marked as read"}

@blp.route("/notifications/read-all")
class NotificationReadAll(MethodView):
    @jwt_required()
    def patch(self):
        user_id = int(get_jwt_identity())
        Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
        db.session.commit()
        return {"message": "All marked as read"}

@blp.route("/notifications/unread-count")
class NotificationUnreadCount(MethodView):
    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())
        count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        return {"unread_count": count}
@blp.route("/notifications/test")
class NotificationTest(MethodView):
    @jwt_required()
    def post(self):
        user_id = int(get_jwt_identity())
        n = Notification(user_id=user_id, message="Test notification", kind="TEST", is_read=False)
        db.session.add(n)
        db.session.commit()
        return {"message": "created"}, 201