import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Callable

from sqlalchemy.orm import Session

from exceptions import CalendarAPIException, DatabaseError, NotFoundError, ValidationError
from logging_config import get_request_id
from models.models import Event, FamilyMembership, Notification, User
from models.notification import NotificationCreate
from services.date_service import calculate_next_occurrence
from services.family_service import ensure_user_in_family, get_user_family_ids
from storage.enums import NotificationType, RepeatType

logger = logging.getLogger(__name__)

EVENT_REMINDER_TYPES = (
    NotificationType.EVENT_REMINDER,
    NotificationType.EVENT_REMINDER_LEGACY,
)


def _normalize_notification_type(
    notification_type: NotificationType | str,
) -> NotificationType:
    if isinstance(notification_type, NotificationType):
        return notification_type
    try:
        return NotificationType(notification_type)
    except ValueError as exc:
        raise ValidationError("Invalid notification type", "type") from exc


def _get_existing_notification(
    db: Session,
    user_id: int,
    event_id: int | None,
    notification_type: NotificationType | str,
    message: str | None = None,
) -> Notification | None:
    normalized_type = _normalize_notification_type(notification_type)
    query = db.query(Notification).filter(
        Notification.user_id == user_id,
    )
    if normalized_type == NotificationType.EVENT_REMINDER:
        query = query.filter(Notification.type.in_(EVENT_REMINDER_TYPES))
    else:
        query = query.filter(Notification.type == normalized_type)
    query = query.filter(Notification.event_id.is_(None) if event_id is None else Notification.event_id == event_id)

    if normalized_type == NotificationType.EVENT_REMINDER and message is not None:
        query = query.filter(Notification.message == message)

    return query.first()


def _create_notification_record(
    db: Session,
    user_id: int,
    event_id: int | None,
    message: str,
    notification_type: NotificationType | str,
) -> tuple[Notification, bool]:
    normalized_type = _normalize_notification_type(notification_type)

    existing_notification = _get_existing_notification(
        db,
        user_id,
        event_id,
        normalized_type,
        message=message,
    )
    if existing_notification:
        return existing_notification, False

    notification = Notification(
        user_id=user_id,
        message=message,
        type=normalized_type,
        event_id=event_id,
        is_read=False,
        created_at=datetime.utcnow(),
        sent=True,
        send_at=datetime.utcnow(),
    )
    db.add(notification)
    return notification, True


def create_notification(db: Session, payload: NotificationCreate, current_user_id: int) -> Notification:
    try:
        event = db.query(Event).filter(Event.id == payload.event_id).first()
        if event is None:
            raise CalendarAPIException("Event not found", 404)

        ensure_user_in_family(db, current_user_id, event.family_id)
        notification, _ = _create_notification_record(
            db=db,
            user_id=current_user_id,
            event_id=event.id,
            message=f"Reminder: {event.title} on {event.next_occurrence}",
            notification_type=NotificationType.EVENT_REMINDER,
        )
        db.commit()
        db.refresh(notification)
        logger.info(
            "Notification created",
            extra={"operation": "create_notification", "user_id": current_user_id, "notification_id": notification.id, "entity_id": notification.id},
        )
        return notification
    except (CalendarAPIException, ValidationError):
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Notification creation failed", exc_info=True)
        raise DatabaseError(f"Failed to create notification: {exc}", "create_notification") from exc


def get_user_notifications(db: Session, user_id: int) -> list[Notification]:
    try:
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )
    except Exception as exc:
        logger.error("Failed to get notifications", exc_info=True)
        raise DatabaseError(f"Failed to get notifications: {exc}", "get_user_notifications") from exc


def mark_notification_as_read(db: Session, notification_id: int, user_id: int) -> Notification:
    try:
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if notification is None:
            raise CalendarAPIException("Notification not found", 404)

        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return notification
    except CalendarAPIException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Failed to mark notification as read", exc_info=True)
        raise DatabaseError(f"Failed to mark notification as read: {exc}", "mark_notification_as_read") from exc


def delete_notification(db: Session, notification_id: int, user_id: int) -> dict[str, str]:
    try:
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if notification is None:
            raise CalendarAPIException("Notification not found", 404)

        db.delete(notification)
        db.commit()
        return {"message": "Notification deleted successfully"}
    except CalendarAPIException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Failed to delete notification", exc_info=True)
        raise DatabaseError(f"Failed to delete notification: {exc}", "delete_notification") from exc


def _notify_family(
    db: Session,
    event: Event,
    message_factory: Callable[[Event], str],
    actor_user_id: int | None,
) -> None:
    memberships = db.query(FamilyMembership).filter(FamilyMembership.family_id == event.family_id).all()
    created_notifications: list[Notification] = []
    for member in memberships:
        if actor_user_id is not None and member.user_id == actor_user_id:
            continue
        notification, created = _create_notification_record(
            db=db,
            user_id=member.user_id,
            event_id=event.id,
            message=message_factory(event),
            notification_type=NotificationType.SYSTEM,
        )
        if created:
            created_notifications.append(notification)

    if created_notifications:
        db.commit()


def notify_family_on_event_created(db: Session, event: Event, actor_user_id: int) -> None:
    _notify_family(db, event, lambda item: f"New event created: {item.title}", actor_user_id)


def notify_family_on_event_updated(db: Session, event: Event, actor_user_id: int | None = None) -> None:
    _notify_family(db, event, lambda item: f"Event updated: {item.title}", actor_user_id)


def notify_family_invitation(db: Session, invited_user_id: int, family_id: int, invited_by_user_id: int) -> None:
    try:
        notification, _ = _create_notification_record(
            db=db,
            user_id=invited_user_id,
            event_id=None,
            message=f"You were invited to family #{family_id} by user #{invited_by_user_id}",
            notification_type=NotificationType.INVITE,
        )
        db.commit()
        db.refresh(notification)
    except Exception:
        db.rollback()
        raise


def _event_occurs_within_window(next_occurrence: date, today: date) -> bool:
    return (next_occurrence - today).days in (0, 1)


def _resolve_occurrence_without_commit(event: Event, today: date) -> date | None:
    current_next_occurrence = event.next_occurrence
    if current_next_occurrence is not None and current_next_occurrence >= today:
        return current_next_occurrence
    return calculate_next_occurrence(event)


def _advance_next_occurrence_after_reminder(event: Event, sent_for_occurrence: date) -> None:
    if event.repeat_type == RepeatType.NONE:
        return

    event.next_occurrence = calculate_next_occurrence(
        event, reference_date=sent_for_occurrence + timedelta(days=1)
    )


def _today_reminder_pairs(db: Session, today: date) -> set[tuple[int, int]]:
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)
    rows = (
        db.query(Notification.event_id, Notification.user_id)
        .filter(
            Notification.type.in_(EVENT_REMINDER_TYPES),
            Notification.event_id.isnot(None),
            Notification.send_at >= start_of_day,
            Notification.send_at < end_of_day,
        )
        .all()
    )
    return {(event_id, user_id) for event_id, user_id in rows if event_id is not None}


def process_event_reminders(db: Session, _within_hours: int = 24) -> int:
    try:
        today = datetime.utcnow().date()
        created_count = 0

        users = db.query(User).all()
        memberships = db.query(FamilyMembership.user_id, FamilyMembership.family_id).all()
        family_ids = sorted({family_id for _, family_id in memberships})
        events = db.query(Event).filter(Event.family_id.in_(family_ids)).all() if family_ids else []

        events_by_family: dict[int, list[Event]] = defaultdict(list)
        for event in events:
            events_by_family[event.family_id].append(event)

        event_occurrences: dict[int, date] = {}
        for event in events:
            next_occurrence = _resolve_occurrence_without_commit(event, today)
            event.next_occurrence = next_occurrence
            if next_occurrence is None:
                continue
            if _event_occurs_within_window(next_occurrence, today):
                event_occurrences[event.id] = next_occurrence

        sent_pairs = _today_reminder_pairs(db, today)
        created_by_event: dict[int, int] = defaultdict(int)

        for user in users:
            user_family_ids = get_user_family_ids(db, user.id)
            for family_id in user_family_ids:
                for event in events_by_family.get(family_id, []):
                    next_occurrence = event_occurrences.get(event.id)
                    if next_occurrence is None:
                        continue
                    if (event.id, user.id) in sent_pairs:
                        continue

                    reminder_message = f"Reminder: {event.title} on {next_occurrence}"
                    notification, created = _create_notification_record(
                        db=db,
                        user_id=user.id,
                        event_id=event.id,
                        message=reminder_message,
                        notification_type=NotificationType.EVENT_REMINDER,
                    )
                    if created:
                        created_count += 1
                        created_by_event[event.id] += 1
                        sent_pairs.add((event.id, user.id))
                        logger.info(
                            "Reminder notification created",
                            extra={
                                "operation": "process_event_reminders",
                                "request_id": get_request_id(),
                                "event_id": event.id,
                                "user_id": user.id,
                                "notification_id": notification.id,
                                "entity_id": notification.id,
                            },
                        )

        for event in events:
            if created_by_event.get(event.id, 0) > 0 and event.id in event_occurrences:
                _advance_next_occurrence_after_reminder(event, event_occurrences[event.id])

        db.commit()
        return created_count
    except Exception as exc:
        db.rollback()
        logger.error("Unexpected error while processing reminders", exc_info=True)
        raise DatabaseError(f"Failed to process reminders: {exc}", "process_event_reminders") from exc


def create_reminder_notifications(db: Session, within_hours: int = 24) -> int:
    return process_event_reminders(db, within_hours)
