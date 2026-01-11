from ..extensions import db
from ..models.startup import Startup, ScoreEvent

def add_score_event(startup_id: int, event_type: str, points: int, note: str | None = None):
    startup = db.session.get(Startup, startup_id)
    if not startup:
        return None

    ev = ScoreEvent(
        startup_id=startup_id,
        event_type=event_type,
        points=points,
        note=note,
    )
    db.session.add(ev)

    startup.score_total = (startup.score_total or 0) + int(points)
    db.session.commit()
    return ev