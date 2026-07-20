import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.models import Notification, PushSubscription, User
from app.services.email_service import send_email
from app.services.notification_preferences_service import get_or_create_preferences
from app.services.notification_templates import resolve_template
from app.services.push_service import send_push_notification

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
                template = resolve_template(notification, user)
                send_email(user.email, template.email_subject, template.email_text_body, template.email_html_body)
            except Exception:
                logger.error("Email failed", exc_info=True, extra={"operation": "dispatch_notification", "notification_id": notification.id})
        if preferences.push_enabled:
            subscriptions = db.query(PushSubscription).filter(PushSubscription.user_id == notification.user_id).all()
            for subscription in subscriptions:
                try:
                    template = resolve_template(notification, user)
                    send_push_notification(db, subscription, template.push_title, template.push_body, template.push_url)
                except Exception:
                    logger.error("Push failed", exc_info=True, extra={"operation": "dispatch_notification", "notification_id": notification.id, "subscription_id": subscription.id})
    except Exception:
        logger.error("Notification dispatch failed", exc_info=True, extra={"operation": "dispatch_notification", "notification_id": notification.id})
