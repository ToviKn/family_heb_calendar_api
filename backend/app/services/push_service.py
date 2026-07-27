import json
import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import PushSubscription

logger = logging.getLogger(__name__)


def _is_expired_exception(exc: Exception) -> bool:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    return status in (404, 410)


def send_push_notification(db: Session, subscription: PushSubscription, title: str, body: str, url: str = "/notifications", icon: str = "/icon-192.png", badge: str = "/badge-72.png") -> bool:
    if not all([settings.vapid_private_key, settings.vapid_public_key, settings.vapid_email]):
        logger.warning("Push skipped: VAPID configuration incomplete", extra={"operation": "send_push_notification"})
        return False
    try:
        from pywebpush import webpush

        webpush(
            subscription_info={"endpoint": subscription.endpoint, "keys": {"p256dh": subscription.p256dh_key, "auth": subscription.auth_key}},
            data=json.dumps({"title": title, "body": body, "url": url, "icon": icon, "badge": badge}),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": f"mailto:{settings.vapid_email}"},
        )
        logger.info("Push sent", extra={"operation": "send_push_notification", "subscription_id": subscription.id})
        return True
    except Exception as exc:
        if _is_expired_exception(exc):
            db.delete(subscription)
            db.commit()
            logger.info("Expired subscription deleted", extra={"operation": "send_push_notification", "subscription_id": subscription.id})
        else:
            logger.error("Push failed", exc_info=True, extra={"operation": "send_push_notification", "subscription_id": subscription.id})
        return False
