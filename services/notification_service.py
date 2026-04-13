import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from logging_config import get_request_id
from models.models import Event, FamilyMembership, Notification, User
from models.notification import NotificationCreate
from services.date_service import calculate_next_occurrence
from storage.enums import RepeatType

logger = logging.getLogger(__name__)


ALLOWED_NOTIFICATION_TYPES = {"event reminder", "invite", "system", "EVENT_REMINDER"}
EVENT_REMINDER_TYPE = "EVENT_REMINDER"


def get_user_family_ids(
    user: User, db: Session, membership_map: dict[int, list[int]] | None = None
) -> list[int]:
    if membership_map is not None:
        return membership_map.get(user.id, [])

    memberships = (
        db.query(FamilyMembership.family_id)
        .filter(FamilyMembership.user_id == user.id)
        .all()
    )
    return [family_id for (family_id,) in memberships]


def _get_existing_notification(
    db: Session,
    user_id: int,
    event_id: int | None,
    notification_type: str,
    message: str | None = None,
) -> Notification | None:
    query = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.type == notification_type,
    )

    if event_id is None:
        query = query.filter(Notification.event_id.is_(None))
    else:
        query = query.filter(Notification.event_id == event_id)

    if notification_type == EVENT_REMINDER_TYPE and message is not None:
        query = query.filter(Notification.message == message)

    return cast(Notification | None, query.first())


def _create_notification_record(
    db: Session,
    user_id: int,
    event_id: int | None,
    message: str,
    notification_type: str,
) -> tuple[Notification, bool]:
    try:
        if notification_type not in ALLOWED_NOTIFICATION_TYPES:
            logger.warning(
                "Invalid notification type",
                extra={
                    "request_id": get_request_id(),
                    "user_id": user_id,
                    "notification_id": None,
                    "type": notification_type,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid notification type",
            )

        existing_notification = _get_existing_notification(
            db,
            user_id,
            event_id,
            notification_type,
            message=message,
        )
        if existing_notification:
            logger.info(
                "Duplicate notification prevented",
                extra={
                    "request_id": get_request_id(),
                    "user_id": user_id,
                    "notification_id": existing_notification.id,
                    "type": notification_type,
                    "event_id": event_id,
                },
            )
            return existing_notification, False

        notification = Notification(
            user_id=user_id,
            message=message,
            type=notification_type,
            event_id=event_id,
            is_read=False,
            created_at=datetime.utcnow(),
            sent=True,
            send_at=datetime.utcnow(),
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        logger.info(
            "Notification created and sent",
            extra={
                "operation": "create_notification_record",
                "request_id": get_request_id(),
                "user_id": notification.user_id,
                "notification_id": notification.id,
                "type": notification.type,
            },
        )
        return notification, True
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.error(
            "Notification failed",
            exc_info=True,
            extra={
                "operation": "create_notification_record",
                "request_id": get_request_id(),
                "user_id": user_id,
                "notification_id": None,
            },
        )
        raise


def create_notification(
    db: Session,
    payload: NotificationCreate,
    current_user_id: int,
) -> Notification:
    try:
        event = cast(Event | None, db.query(Event).filter(Event.id == payload.event_id).first())
        if not event:
            logger.warning(
                "Notification creation rejected: event not found",
                extra={
                    "request_id": get_request_id(),
                    "user_id": current_user_id,
                    "notification_id": None,
                    "event_id": payload.event_id,
                },
            )
            raise HTTPException(status_code=404, detail="Event not found")

        membership = (
            db.query(FamilyMembership)
            .filter(
                FamilyMembership.user_id == current_user_id,
                FamilyMembership.family_id == event.family_id,
            )
            .first()
        )
        if not membership:
            logger.warning(
                "Notification creation rejected: user not in event family",
                extra={
                    "request_id": get_request_id(),
                    "user_id": current_user_id,
                    "notification_id": None,
                    "event_id": payload.event_id,
                    "family_id": event.family_id,
                },
            )
            raise HTTPException(status_code=403, detail="User not in event family")

        return _create_notification_record(
            db=db,
            user_id=current_user_id,
            event_id=event.id,
            message=f"Reminder: {event.title} on {event.next_occurrence}",
            notification_type=EVENT_REMINDER_TYPE,
        )[0]
    except HTTPException:
        raise
    except Exception:
        logger.error(
            "Notification failed",
            exc_info=True,
            extra={
                "request_id": get_request_id(),
                "user_id": current_user_id,
                "notification_id": None,
                "event_id": payload.event_id,
            },
        )
        raise


def get_user_notifications(db: Session, user_id: int) -> list[Notification]:
    try:
        notifications = cast(
            list[Notification],
            (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
            ),
        )
        logger.info(
            "Notifications fetched",
            extra={
                "operation": "get_user_notifications",
                "request_id": get_request_id(),
                "user_id": user_id,
                "notification_id": None,
            },
        )
        return notifications
    except Exception:
        logger.error(
            "Notification failed",
            exc_info=True,
            extra={
                "operation": "get_user_notifications",
                "request_id": get_request_id(),
                "user_id": user_id,
                "notification_id": None,
            },
        )
        raise


def mark_notification_as_read(
    db: Session, notification_id: int, user_id: int
) -> Notification:
    try:
        notification = cast(
            Notification | None,
            (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
            ),
        )
        if not notification:
            logger.warning(
                "Notification mark-as-read rejected",
                extra={
                    "request_id": get_request_id(),
                    "user_id": user_id,
                    "notification_id": notification_id,
                },
            )
            raise HTTPException(status_code=404, detail="Notification not found")

        notification.is_read = True
        db.commit()
        db.refresh(notification)

        logger.info(
            "Notification marked as read",
            extra={
                "operation": "mark_notification_as_read",
                "request_id": get_request_id(),
                "user_id": user_id,
                "notification_id": notification.id,
            },
        )
        return notification
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.error(
            "Notification failed",
            exc_info=True,
            extra={
                "operation": "mark_notification_as_read",
                "request_id": get_request_id(),
                "user_id": user_id,
                "notification_id": notification_id,
            },
        )
        raise


def delete_notification(db: Session, notification_id: int, user_id: int) -> dict[str, str]:
    try:
        notification = cast(
            Notification | None,
            (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
            ),
        )
        if not notification:
            logger.warning(
                "Notification delete rejected",
                extra={
                    "request_id": get_request_id(),
                    "user_id": user_id,
                    "notification_id": notification_id,
                },
            )
            raise HTTPException(status_code=404, detail="Notification not found")

        db.delete(notification)
        db.commit()
        logger.info(
            "Notification deleted",
            extra={
                "operation": "delete_notification",
                "request_id": get_request_id(),
                "user_id": user_id,
                "notification_id": notification_id,
            },
        )

        return {"message": "Notification deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.error(
            "Notification failed",
            exc_info=True,
            extra={
                "operation": "delete_notification",
                "request_id": get_request_id(),
                "user_id": user_id,
                "notification_id": notification_id,
            },
        )
        raise


def notify_family_on_event_created(db: Session, event: Event, actor_user_id: int) -> None:
    memberships = (
        db.query(FamilyMembership)
        .filter(FamilyMembership.family_id == event.family_id)
        .all()
    )
    for member in memberships:
        if member.user_id == actor_user_id:
            continue
        _create_notification_record(
            db=db,
            user_id=member.user_id,
            event_id=event.id,
            message=f"New event created: {event.title}",
            notification_type="system",
        )


def notify_family_on_event_updated(
    db: Session, event: Event, actor_user_id: int | None = None
) -> None:
    memberships = (
        db.query(FamilyMembership)
        .filter(FamilyMembership.family_id == event.family_id)
        .all()
    )
    for member in memberships:
        if actor_user_id is not None and member.user_id == actor_user_id:
            continue
        _create_notification_record(
            db=db,
            user_id=member.user_id,
            event_id=event.id,
            message=f"Event updated: {event.title}",
            notification_type="system",
        )


def notify_family_invitation(
    db: Session, invited_user_id: int, family_id: int, invited_by_user_id: int
) -> None:
    _create_notification_record(
        db=db,
        user_id=invited_user_id,
        event_id=None,
        message=f"You were invited to family #{family_id} by user #{invited_by_user_id}",
        notification_type="invite",
    )


def _event_occurs_within_window(next_occurrence: date, today: date) -> tuple[bool, str]:
    days_diff = (next_occurrence - today).days

    if days_diff == 0:
        return True, "event occurs today"
    if days_diff == 1:
        return True, "event occurs within reminder window"
    return False, "event outside reminder window"



def _reminder_sent_today(db: Session, event_id: int, user_id: int, today: date) -> bool:
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)
    return (
        db.query(Notification)
        .filter(
            Notification.event_id == event_id,
            Notification.user_id == user_id,
            Notification.type == EVENT_REMINDER_TYPE,
            Notification.send_at >= start_of_day,
            Notification.send_at < end_of_day,
        )
        .first()
        is not None
    )

def _resolve_next_occurrence(db: Session, event: Event, today: date) -> date | None:
    current_next_occurrence = cast(date | None, event.next_occurrence)
    if current_next_occurrence is not None and current_next_occurrence >= today:
        return current_next_occurrence

    next_occurrence = calculate_next_occurrence(event)
    if next_occurrence is None:
        if current_next_occurrence is not None:
            event.next_occurrence = None
            db.add(event)
            db.commit()
            db.refresh(event)
        return None

    if current_next_occurrence != next_occurrence:
        event.next_occurrence = next_occurrence
        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info(
            "Next occurrence recalculated for reminder processing",
            extra={
                "request_id": get_request_id(),
                "event_id": event.id,
                "user_id": None,
                "notification_id": None,
                "next_occurrence": next_occurrence.isoformat(),
            },
        )
    return next_occurrence


def _advance_next_occurrence_after_reminder(
    db: Session, event: Event, sent_for_occurrence: date
) -> None:
    if event.repeat_type == RepeatType.NONE:
        return

    next_occurrence = calculate_next_occurrence(
        event, reference_date=sent_for_occurrence + timedelta(days=1)
    )
    if next_occurrence == event.next_occurrence:
        return

    event.next_occurrence = next_occurrence
    db.add(event)
    db.commit()
    db.refresh(event)


def process_event_reminders(db: Session, _within_hours: int = 24) -> int:
    try:
        today = datetime.utcnow().date()
        created_count = 0
        created_by_event: dict[int, int] = defaultdict(int)

        users = cast(list[User], db.query(User).all())
        memberships = cast(
            list[tuple[int, int]],
            db.query(FamilyMembership.user_id, FamilyMembership.family_id).all(),
        )
        user_family_map: dict[int, list[int]] = defaultdict(list)
        for user_id, family_id in memberships:
            user_family_map[user_id].append(family_id)

        all_family_ids = sorted({family_id for _, family_id in memberships})
        events = cast(
            list[Event],
            db.query(Event).filter(Event.family_id.in_(all_family_ids)).all()
            if all_family_ids
            else [],
        )
        events_by_family: dict[int, list[Event]] = defaultdict(list)
        for event in events:
            events_by_family[event.family_id].append(event)

        event_occurrences: dict[int, date] = {}
        for event in events:
            next_occurrence = _resolve_next_occurrence(db, event, today)
            if next_occurrence is None:
                continue
            should_send, _ = _event_occurs_within_window(next_occurrence, today)
            if should_send:
                event_occurrences[event.id] = next_occurrence

        for user in users:
            family_ids = get_user_family_ids(user, db, user_family_map)
            if not family_ids:
                logger.warning(
                    "Reminder processing skipped: user has no families",
                    extra={
                        "request_id": get_request_id(),
                        "user_id": user.id,
                        "notification_id": None,
                    },
                )
                continue

            user_events = [
                event
                for family_id in family_ids
                for event in events_by_family.get(family_id, [])
            ]
            logger.info(
                "Reminder processing for user",
                extra={
                    "request_id": get_request_id(),
                    "user_id": user.id,
                    "notification_id": None,
                    "event_count": len(user_events),
                },
            )

            for event in user_events:
                next_occurrence = event_occurrences.get(event.id)
                if next_occurrence is None:
                    continue
                if _reminder_sent_today(db, event.id, user.id, today):
                    continue

                reminder_message = f"Reminder: {event.title} on {next_occurrence}"
                notification, created = _create_notification_record(
                    db=db,
                    user_id=user.id,
                    event_id=event.id,
                    message=reminder_message,
                    notification_type=EVENT_REMINDER_TYPE,
                )
                if created:
                    created_count += 1
                    created_by_event[event.id] += 1
                    logger.info(
                        "Reminder notification created",
                        extra={
                            "request_id": get_request_id(),
                            "event_id": event.id,
                            "user_id": user.id,
                            "notification_id": notification.id,
                            "next_occurrence": next_occurrence.isoformat(),
                        },
                    )

        for event in events:
            if created_by_event.get(event.id, 0) > 0 and event.id in event_occurrences:
                _advance_next_occurrence_after_reminder(
                    db, event, event_occurrences[event.id]
                )

        return created_count
    except Exception:
        logger.error(
            "Unexpected error while processing reminders",
            exc_info=True,
            extra={"request_id": get_request_id(), "notification_id": None},
        )
        raise


def create_reminder_notifications(db: Session, within_hours: int = 24) -> int:
    return process_event_reminders(db, within_hours)
