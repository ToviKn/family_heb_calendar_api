import logging
from datetime import date, datetime, timedelta
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from logging_config import get_request_id
from models.models import Event, FamilyMembership, Notification
from models.notification import NotificationCreate
from services.date_service import calculate_next_occurrence
from storage.enums import RepeatType

logger = logging.getLogger(__name__)


ALLOWED_NOTIFICATION_TYPES = {"event reminder", "invite", "system", "EVENT_REMINDER"}
EVENT_REMINDER_TYPE = "EVENT_REMINDER"


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



def _reminder_sent_today(db: Session, event_id: int, today: date) -> bool:
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)
    return (
        db.query(Notification)
        .filter(
            Notification.event_id == event_id,
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
    today = datetime.utcnow().date()
    events = cast(list[Event], db.query(Event).all())
    created_count = 0

    for event in events:
        next_occurrence = _resolve_next_occurrence(db, event, today)
        if next_occurrence is None:
            logger.info(
                "Reminder skipped: no next occurrence",
                extra={
                    "request_id": get_request_id(),
                    "event_id": event.id,
                    "user_id": None,
                    "notification_id": None,
                },
            )
            continue

        should_send, reason = _event_occurs_within_window(next_occurrence, today)
        if should_send and _reminder_sent_today(db, event.id, today):
            should_send = False
            reason = "reminder already sent today"
        if not should_send:
            logger.info(
                "Reminder skipped: event outside reminder window",
                extra={
                    "request_id": get_request_id(),
                    "event_id": event.id,
                    "user_id": None,
                    "notification_id": None,
                    "next_occurrence": next_occurrence.isoformat(),
                    "reason": reason,
                },
            )
            continue

        memberships = (
            db.query(FamilyMembership)
            .filter(FamilyMembership.family_id == event.family_id)
            .all()
        )
        if not memberships:
            logger.info(
                "Reminder skipped: no family members found",
                extra={
                    "request_id": get_request_id(),
                    "event_id": event.id,
                    "user_id": None,
                    "notification_id": None,
                    "family_id": event.family_id,
                },
            )
            continue

        created_for_event = 0
        reminder_message = f"Reminder: {event.title} on {next_occurrence}"
        for member in memberships:
            notification, created = _create_notification_record(
                db=db,
                user_id=member.user_id,
                event_id=event.id,
                message=reminder_message,
                notification_type=EVENT_REMINDER_TYPE,
            )
            if created:
                created_count += 1
                created_for_event += 1
                logger.info(
                    "Reminder notification created",
                    extra={
                        "request_id": get_request_id(),
                        "event_id": event.id,
                        "user_id": member.user_id,
                        "notification_id": notification.id,
                        "next_occurrence": next_occurrence.isoformat(),
                        "reason": reason,
                    },
                )

        if created_for_event > 0:
            _advance_next_occurrence_after_reminder(db, event, next_occurrence)

    return created_count


def create_reminder_notifications(db: Session, within_hours: int = 24) -> int:
    return process_event_reminders(db, within_hours)
