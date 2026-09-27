import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.models import Notification, PushSubscription, User
from app.services.email_service import send_email
from app.services.notification_preferences_service import get_or_create_preferences
from app.services.notification_templates import resolve_template
from app.services.push_service import send_push_notification
from app.utils.timezone import application_today

logger = logging.getLogger(__name__)


def _reminder_log_context(notification: Notification) -> dict[str, object]:
    metadata = notification.metadata_json or {}
    return {
        "notification_id": notification.id,
        "user_id": notification.user_id,
        "event_id": notification.event_id,
        "reminder_type": metadata.get("reminder_type"),
    }


def _is_event_reminder(notification: Notification) -> bool:
    return (notification.metadata_json or {}).get("notification_kind") == "event_reminder"


def _days_until(notification: Notification) -> int | None:
    metadata = notification.metadata_json or {}
    occurrence = metadata.get("occurrence_date") or metadata.get("date")
    if not isinstance(occurrence, str):
        return None
    try:
        return (date.fromisoformat(occurrence) - application_today()).days
    except ValueError:
        return None


def dispatch_notification(db: Session, notification: Notification) -> None:
    reminder_context = _reminder_log_context(notification)
    is_reminder = _is_event_reminder(notification)
    try:
        user = db.get(User, notification.user_id)
        if user is None:
            return
        preferences = get_or_create_preferences(db, notification.user_id)
        days = _days_until(notification)
        if days == 0 and not preferences.notify_today:
            if is_reminder:
                logger.info("Reminder dispatch skipped: preference disabled", extra=reminder_context)
            return
        if days == 1 and not preferences.notify_day_before:
            if is_reminder:
                logger.info("Reminder dispatch skipped: preference disabled", extra=reminder_context)
            return

        if is_reminder:
            logger.info("Reminder dispatch started", extra=reminder_context)
        if preferences.email_enabled:
            try:
                template = resolve_template(notification, user)
                email_sent = send_email(user.email, template.email_subject, template.email_text_body, template.email_html_body)
                if is_reminder:
                    logger.info(
                        "Reminder email sent" if email_sent else "Reminder dispatch failed",
                        extra=reminder_context,
                    )
            except Exception:
                logger.error(
                    "Reminder dispatch failed" if is_reminder else "Email failed",
                    exc_info=True,
                    extra=reminder_context if is_reminder else {"operation": "dispatch_notification", "notification_id": notification.id},
                )
        if preferences.push_enabled:
            subscriptions = db.query(PushSubscription).filter(PushSubscription.user_id == notification.user_id).all()
            for subscription in subscriptions:
                try:
                    template = resolve_template(notification, user)
                    send_push_notification(db, subscription, template.push_title, template.push_body, template.push_url)
                except Exception:
                    logger.error("Push failed", exc_info=True, extra={"operation": "dispatch_notification", "notification_id": notification.id, "subscription_id": subscription.id})
    except Exception:
        logger.error(
            "Reminder dispatch failed" if is_reminder else "Notification dispatch failed",
            exc_info=True,
            extra=reminder_context if is_reminder else {"operation": "dispatch_notification", "notification_id": notification.id},
        )
