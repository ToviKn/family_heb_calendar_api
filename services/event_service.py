import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from exceptions import CalendarAPIException, DatabaseError, NotFoundError
from models.event import EventCreate, EventUpdate
from models.models import Event
from services import notification_service
from services.date_service import calculate_next_occurrence, convert_to_hebrew
from services.family_service import ensure_user_in_family

logger = logging.getLogger(__name__)


def create_event(db: Session, event: EventCreate, user_id: int) -> Event:
    try:
        ensure_user_in_family(db, user_id, event.family_id)

        db_event = Event(
            title=event.title,
            description=event.description,
            year=event.year,
            month=event.month,
            day=event.day,
            start_time=event.start_time,
            end_time=event.end_time,
            calendar_type=event.calendar_type,
            repeat_type=event.repeat_type,
            family_id=event.family_id,
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db_event.next_occurrence = calculate_next_occurrence(db_event)

        db.add(db_event)
        db.commit()
        db.refresh(db_event)

        logger.info(
            "Event created",
            extra={"operation": "create_event", "event_id": db_event.id, "family_id": db_event.family_id, "user_id": user_id},
        )
        notification_service.notify_family_on_event_created(db, db_event, user_id)
        return db_event
    except CalendarAPIException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error(
            "Failed to create event",
            exc_info=True,
            extra={"operation": "create_event", "family_id": event.family_id, "user_id": user_id},
        )
        raise DatabaseError(f"Failed to create event: {exc}", "create_event") from exc


def get_events_for_date(
    db: Session, year: int, month: int, day: int, family_ids: list[int] | None = None
) -> list[Event]:
    try:
        _, h_month, h_day = convert_to_hebrew(year, month, day)
        if family_ids is not None and not family_ids:
            return []

        gregorian_query = db.query(Event).filter(
            and_(Event.calendar_type == "gregorian", Event.month == month, Event.day == day)
        )
        hebrew_query = db.query(Event).filter(
            and_(Event.calendar_type == "hebrew", Event.month == h_month, Event.day == h_day)
        )

        if family_ids is not None:
            gregorian_query = gregorian_query.filter(Event.family_id.in_(family_ids))
            hebrew_query = hebrew_query.filter(Event.family_id.in_(family_ids))

        results = [*gregorian_query.all(), *hebrew_query.all()]
        logger.info(
            "Events fetched by date",
            extra={"operation": "get_events_for_date", "user_id": None, "entity_id": None, "result_count": len(results)},
        )
        return results
    except CalendarAPIException:
        raise
    except Exception as exc:
        logger.error("Failed to get events for date", exc_info=True)
        raise DatabaseError(f"Failed to retrieve events: {exc}", "get_events_for_date") from exc


def get_event_by_id(db: Session, event_id: int, user_id: int | None = None) -> Event:
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if event is None:
            raise NotFoundError("Event", event_id)
        if user_id is not None:
            ensure_user_in_family(db, user_id, event.family_id)
        return event
    except CalendarAPIException:
        raise
    except Exception as exc:
        logger.error("Failed to get event", exc_info=True, extra={"operation": "get_event_by_id", "event_id": event_id})
        raise DatabaseError(f"Failed to retrieve event: {exc}", "get_event_by_id") from exc


def delete_event(db: Session, event_id: int, user_id: int) -> dict[str, str]:
    try:
        event = get_event_by_id(db, event_id, user_id=user_id)
        if event.created_by != user_id:
            raise CalendarAPIException("Not authorized to delete this event", 403)

        db.delete(event)
        db.commit()
        logger.info(
            "Event deleted",
            extra={"operation": "delete_event", "event_id": event_id, "user_id": user_id, "entity_id": event_id},
        )
        return {"message": "Event deleted successfully"}
    except CalendarAPIException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Failed to delete event", exc_info=True)
        raise DatabaseError(f"Failed to delete event: {exc}", "delete_event") from exc


def update_event(db: Session, event_id: int, updated_event: EventUpdate, user_id: int) -> Event:
    try:
        event = get_event_by_id(db, event_id, user_id=user_id)
        if event.created_by != user_id:
            raise CalendarAPIException("Not authorized to update this event", 403)

        update_data = updated_event.model_dump(exclude_unset=True)
        if "end_time" in update_data and "start_time" not in update_data:
            update_data["start_time"] = event.start_time
        if "start_time" in update_data and "end_time" not in update_data:
            update_data["end_time"] = event.end_time

        for field, value in update_data.items():
            setattr(event, field, value)

        if any(field in update_data for field in ["year", "month", "day", "calendar_type", "repeat_type"]):
            event.next_occurrence = calculate_next_occurrence(event)

        db.commit()
        db.refresh(event)
        notification_service.notify_family_on_event_updated(db, event, actor_user_id=user_id)
        logger.info(
            "Event updated",
            extra={"operation": "update_event", "event_id": event_id, "user_id": user_id, "entity_id": event_id},
        )
        return event
    except CalendarAPIException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Failed to update event", exc_info=True)
        raise DatabaseError(f"Failed to update event: {exc}", "update_event") from exc


def get_upcoming_events(
    db: Session,
    days: int = 30,
    family_id: int | None = None,
    allowed_family_ids: list[int] | None = None,
) -> list[Event]:
    try:
        if allowed_family_ids is not None and not allowed_family_ids:
            return []
        if family_id is not None and allowed_family_ids is not None and family_id not in allowed_family_ids:
            return []

        today = date.today()
        end_date = today + timedelta(days=days)
        query = db.query(Event).filter(and_(Event.next_occurrence >= today, Event.next_occurrence <= end_date))

        if allowed_family_ids is not None:
            query = query.filter(Event.family_id.in_(allowed_family_ids))
        if family_id:
            query = query.filter(Event.family_id == family_id)

        return query.order_by(Event.next_occurrence).all()
    except Exception as exc:
        logger.error("Failed to get upcoming events", exc_info=True)
        raise DatabaseError(f"Failed to retrieve upcoming events: {exc}", "get_upcoming_events") from exc


def get_events_by_family(
    db: Session,
    family_id: int,
    page: int = 1,
    per_page: int = 20,
    allowed_family_ids: list[int] | None = None,
) -> dict[str, Any]:
    try:
        if allowed_family_ids is not None and family_id not in allowed_family_ids:
            return {"events": [], "total": 0, "page": page, "per_page": per_page}

        offset = (page - 1) * per_page
        query = db.query(Event).filter(Event.family_id == family_id)
        total = query.count()
        events = query.offset(offset).limit(per_page).all()
        return {"events": events, "total": total, "page": page, "per_page": per_page}
    except Exception as exc:
        logger.error("Failed to get family events", exc_info=True)
        raise DatabaseError(f"Failed to retrieve family events: {exc}", "get_events_by_family") from exc
