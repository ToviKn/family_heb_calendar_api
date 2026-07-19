import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.models import Notification, PushSubscription, User
from app.services.email_service import send_event_reminder
from app.services.notification_preferences_service import get_or_create_preferences
from app.services.push_service import send_push_notification
from app.storage.enums import NotificationType

logger = logging.getLogger(__name__)


def _days_until(notification: Notification) -> int | None:
    metadata = notification.metadata_json or {}
    occurrence = metadata.get("occurrence_date") or metadata.get("date")
    if not isinstance(occurrence, str):
        return None
    try:
        return (date.fromisoformat(occurrence) - date.today()).days
    except ValueError:
        return None


def dispatch_notification(db: Session, notification: Notification) -> None:
    try:
        if notification.type != NotificationType.EVENT_REMINDER.value:
            return
        user = db.get(User, notification.user_id)
        if user is None:
            return
        preferences = get_or_create_preferences(db, notification.user_id)
        days = _days_until(notification)
        if days == 0 and not preferences.notify_today:
            return
        if days == 1 and not preferences.notify_day_before:
            return

        if preferences.email_enabled:
            try:
                send_event_reminder(user, notification)
            except Exception:
                logger.error("Email failed", exc_info=True, extra={"operation": "dispatch_notification", "notification_id": notification.id})
        if preferences.push_enabled:
            subscriptions = db.query(PushSubscription).filter(PushSubscription.user_id == notification.user_id).all()
            for subscription in subscriptions:
                try:
                    send_push_notification(db, subscription, "Family Calendar", notification.message.replace("Reminder: ", ""), "/notifications")
                except Exception:
                    logger.error("Push failed", exc_info=True, extra={"operation": "dispatch_notification", "notification_id": notification.id, "subscription_id": subscription.id})
    except Exception:
        logger.error("Notification dispatch failed", exc_info=True, extra={"operation": "dispatch_notification", "notification_id": notification.id})
