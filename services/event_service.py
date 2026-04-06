import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from exceptions import CalendarAPIException, DatabaseError, NotFoundError
from models.event import EventCreate, EventUpdate
from models.models import Event, FamilyMembership, User
from services.date_service import calculate_next_occurrence, convert_to_hebrew
from services import notification_service

logger = logging.getLogger(__name__)


def get_user_family_ids(user: User, db: Session) -> list[int]:
    """Return all family ids where the user is a member."""
    memberships = (
        db.query(FamilyMembership.family_id)
        .filter(FamilyMembership.user_id == user.id)
        .all()
    )
    family_ids = [family_id for (family_id,) in memberships]
    logger.debug(
        "Resolved user family memberships",
        extra={"operation": "get_user_family_ids", "user_id": user.id, "family_count": len(family_ids)},
    )
    return family_ids


def create_event(db: Session, event: EventCreate, user_id: int) -> Event:
    """Create a new event with proper validation and error handling"""
    try:
        membership = (
            db.query(FamilyMembership)
            .filter(
                FamilyMembership.user_id == user_id,
                FamilyMembership.family_id == event.family_id,
            )
            .first()
        )

        if not membership:
            logger.warning(
                "Event creation blocked: user not in family",
                extra={"user_id": user_id, "family_id": event.family_id},
            )
            raise HTTPException(status_code=403, detail="User not in family")

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
            extra={
                "operation": "create_event",
                "event_id": db_event.id,
                "family_id": db_event.family_id,
                "user_id": user_id,
            },
        )
        notification_service.notify_family_on_event_created(db, db_event, user_id)
        return db_event

    except (HTTPException, CalendarAPIException):
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create event",
            exc_info=True,
            extra={"operation": "create_event", "family_id": event.family_id, "created_by": user_id},
        )
        raise DatabaseError(f"Failed to create event: {str(e)}", "create")


def get_events_for_date(
    db: Session, year: int, month: int, day: int, family_ids: Optional[list[int]] = None
) -> list[Event]:
    """Efficiently get events for a specific date using database queries"""
    try:
        _, h_month, h_day = convert_to_hebrew(year, month, day)
        logger.debug(
            "Querying events for date",
            extra={
                "year": year,
                "month": month,
                "day": day,
                "h_month": h_month,
                "h_day": h_day,
            },
        )

        if family_ids is not None and not family_ids:
            logger.info(
                "Events fetched by date",
                extra={"operation": "get_events_for_date", "result_count": 0},
            )
            return []

        gregorian_query = (
            db.query(Event)
            .filter(
                and_(
                    Event.calendar_type == "gregorian",
                    Event.month == month,
                    Event.day == day,
                )
            )
        )
        hebrew_query = (
            db.query(Event)
            .filter(
                and_(
                    Event.calendar_type == "hebrew",
                    Event.month == h_month,
                    Event.day == h_day,
                )
            )
        )

        if family_ids is not None:
            gregorian_query = gregorian_query.filter(Event.family_id.in_(family_ids))
            hebrew_query = hebrew_query.filter(Event.family_id.in_(family_ids))

        gregorian_events = gregorian_query.all()
        hebrew_events = hebrew_query.all()

        results = cast(list[Event], gregorian_events + hebrew_events)
        logger.info(
            "Events fetched by date",
            extra={"operation": "get_events_for_date", "result_count": len(results)},
        )
        return results

    except Exception as e:
        logger.error(
            "Failed to get events for date",
            exc_info=True,
            extra={"operation": "get_events_for_date", "year": year, "month": month, "day": day},
        )
        raise DatabaseError(
            f"Failed to retrieve events: {str(e)}", "get_events_for_date"
        )


def get_event_by_id(db: Session, event_id: int) -> Event:
    """Get a single event by ID"""
    try:
        event = cast(Event | None, db.query(Event).filter(Event.id == event_id).first())
        if not event:
            raise NotFoundError("Event", event_id)
        return event
    except NotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to get event", exc_info=True, extra={"event_id": event_id})
        raise DatabaseError(f"Failed to retrieve event: {str(e)}", "get_event_by_id")


def delete_event(db: Session, event_id: int, user_id: int) -> dict[str, str]:
    """Delete an event with proper error handling"""
    try:
        event = get_event_by_id(db, event_id)
        if event.created_by != user_id:
            logger.warning(
                "Unauthorized event delete attempt",
                extra={
                    "operation": "delete_event",
                    "event_id": event_id,
                    "family_id": event.family_id,
                    "user_id": user_id,
                    "created_by": event.created_by,
                },
            )
            raise HTTPException(status_code=403, detail="Not authorized to delete this event")

        db.delete(event)
        db.commit()

        logger.info(
            "Event deleted",
            extra={"operation": "delete_event", "event_id": event_id, "family_id": event.family_id, "user_id": user_id},
        )
        return {"message": "Event deleted successfully"}
    except HTTPException:
        db.rollback()
        raise
    except NotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to delete event", exc_info=True, extra={"operation": "delete_event", "event_id": event_id}
        )
        raise DatabaseError(f"Failed to delete event: {str(e)}", "delete")


def update_event(db: Session, event_id: int, updated_event: EventUpdate, user_id: int) -> Event:
    """Update an event with partial updates and validation"""
    try:
        event = get_event_by_id(db, event_id)
        if event.created_by != user_id:
            logger.warning(
                "Unauthorized event update attempt",
                extra={
                    "operation": "update_event",
                    "event_id": event_id,
                    "family_id": event.family_id,
                    "user_id": user_id,
                    "created_by": event.created_by,
                },
            )
            raise HTTPException(status_code=403, detail="Not authorized to update this event")
        update_data = updated_event.model_dump(exclude_unset=True)

        if "end_time" in update_data and "start_time" not in update_data:
            update_data["start_time"] = event.start_time
        if "start_time" in update_data and "end_time" not in update_data:
            update_data["end_time"] = event.end_time

        for field, value in update_data.items():
            setattr(event, field, value)

        if any(
            field in update_data
            for field in ["year", "month", "day", "calendar_type", "repeat_type"]
        ):
            event.next_occurrence = calculate_next_occurrence(event)

        db.commit()
        db.refresh(event)

        logger.info(
            "Event updated",
            extra={
                "operation": "update_event",
                "event_id": event_id,
                "family_id": event.family_id,
                "user_id": user_id,
                "updated_fields": sorted(update_data.keys()),
            },
        )
        notification_service.notify_family_on_event_updated(
            db, event, actor_user_id=user_id
        )
        return event
    except HTTPException:
        db.rollback()
        raise
    except NotFoundError:
        db.rollback()
        raise
    except CalendarAPIException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to update event", exc_info=True, extra={"operation": "update_event", "event_id": event_id}
        )
        raise DatabaseError(f"Failed to update event: {str(e)}", "update")


def get_upcoming_events(
    db: Session,
    days: int = 30,
    family_id: Optional[int] = None,
    allowed_family_ids: Optional[list[int]] = None,
) -> list[Event]:
    """Get upcoming events for the next N days"""
    try:
        today = date.today()
        end_date = today + timedelta(days=days)

        if allowed_family_ids is not None and not allowed_family_ids:
            logger.info(
                "Upcoming events fetched",
                extra={"operation": "get_upcoming_events", "days": days, "family_id": family_id, "result_count": 0},
            )
            return []

        query = db.query(Event).filter(
            and_(Event.next_occurrence >= today, Event.next_occurrence <= end_date)
        )

        if allowed_family_ids is not None:
            query = query.filter(Event.family_id.in_(allowed_family_ids))

        if family_id:
            query = query.filter(Event.family_id == family_id)

        events = cast(list[Event], query.order_by(Event.next_occurrence).all())
        logger.info(
            "Upcoming events fetched",
            extra={"operation": "get_upcoming_events", "days": days, "family_id": family_id, "result_count": len(events)},
        )
        return events

    except Exception as e:
        logger.error(
            "Failed to get upcoming events",
            exc_info=True,
            extra={"operation": "get_upcoming_events", "days": days, "family_id": family_id},
        )
        raise DatabaseError(
            f"Failed to retrieve upcoming events: {str(e)}", "get_upcoming"
        )


def get_events_by_family(
    db: Session,
    family_id: int,
    page: int = 1,
    per_page: int = 20,
    allowed_family_ids: Optional[list[int]] = None,
) -> dict[str, Any]:
    """Get paginated events for a specific family"""
    try:
        offset = (page - 1) * per_page

        query = db.query(Event).filter(Event.family_id == family_id)
        if allowed_family_ids is not None and family_id not in allowed_family_ids:
            logger.warning(
                "Unauthorized family events access attempt",
                extra={"operation": "get_events_by_family", "family_id": family_id},
            )
            return {"events": [], "total": 0, "page": page, "per_page": per_page}
        total = query.count()
        events = query.offset(offset).limit(per_page).all()

        logger.info(
            "Family events fetched",
            extra={
                "operation": "get_events_by_family",
                "family_id": family_id,
                "page": page,
                "per_page": per_page,
                "result_count": len(events),
            },
        )

        return {
            "events": events,
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    except Exception as e:
        logger.error(
            "Failed to get events by family",
            exc_info=True,
            extra={"operation": "get_events_by_family", "family_id": family_id, "page": page, "per_page": per_page},
        )
        raise DatabaseError(
            f"Failed to retrieve family events: {str(e)}", "get_events_by_family"
        )
