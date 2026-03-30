import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.models import (
    Event,
    EventParticipant,
    Family,
    FamilyMembership,
    Notification,
    User,
)
from storage.database import get_db

router = APIRouter(prefix="/debug", tags=["debug"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/database")
def debug_database(db: DbSession) -> dict[str, list[dict[str, Any]]]:
    logger.info("Debug database dump requested", extra={"operation": "debug_database"})
    users = db.query(User).all()
    families = db.query(Family).all()
    memberships = db.query(FamilyMembership).all()
    events = db.query(Event).all()
    participants = db.query(EventParticipant).all()
    notifications = db.query(Notification).all()

    payload = {
        "users": [{"id": u.id, "email": u.email, "name": u.name} for u in users],
        "families": [{"id": f.id, "name": f.name} for f in families],
        "memberships": [
            {"user_id": m.user_id, "family_id": m.family_id, "role": m.role}
            for m in memberships
        ],
        "events": [
            {
                "id": e.id,
                "title": e.title,
                "family_id": e.family_id,
                "created_by": e.created_by,
                "date": f"{e.year}-{e.month}-{e.day}",
            }
            for e in events
        ],
        "participants": [
            {"event_id": p.event_id, "user_id": p.user_id, "status": p.status}
            for p in participants
        ],
        "notifications": [
            {"id": n.id, "user_id": n.user_id, "event_id": n.event_id, "type": n.type, "message": n.message, "is_read": n.is_read, "sent": n.sent}
            for n in notifications
        ],
    }
    logger.info(
        "Debug database dump completed",
        extra={
            "operation": "debug_database",
            "users_count": len(users),
            "families_count": len(families),
            "events_count": len(events),
            "notifications_count": len(notifications),
        },
    )
    return payload
