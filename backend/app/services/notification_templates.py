from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Callable

from app.models.models import Notification, User
from app.storage.enums import NotificationType


@dataclass(frozen=True)
class NotificationTemplate:
    email_subject: str
    email_text_body: str
    email_html_body: str
    push_title: str
    push_body: str
    push_url: str = "/notifications"


def _metadata(notification: Notification) -> dict:
    return notification.metadata_json or {}


def _name(payload: object, fallback: str) -> str:
    if isinstance(payload, dict) and isinstance(payload.get("name"), str):
        return payload["name"]
    return fallback


def _event_title(notification: Notification) -> str:
    metadata = _metadata(notification)
    value = metadata.get("event_title")
    if isinstance(value, str) and value:
        return value
    return notification.message.removeprefix("Reminder: ")


def _family_name(notification: Notification) -> str:
    metadata = _metadata(notification)
    value = metadata.get("family_name")
    return value if isinstance(value, str) and value else "your family"


def _base_email(user: User, heading: str, body: str) -> tuple[str, str]:
    first_name = user.name.split()[0] if user.name else "there"
    text = f"Hello {first_name}\n\n{body}\n\nOpen the application to view details."
    html = (
        f"<p>Hello {escape(first_name)}</p>"
        f"<p><strong>{escape(heading)}</strong></p>"
        f"<p>{escape(body)}</p>"
        "<p>Open the application to view details.</p>"
    )
    return text, html


def _event_reminder(notification: Notification, user: User) -> NotificationTemplate:
    title = _event_title(notification)
    body = f"This is a reminder that {title} occurs today."
    text, html = _base_email(user, "Family Calendar Reminder", body)
    return NotificationTemplate(
        email_subject="Family Calendar Reminder",
        email_text_body=text,
        email_html_body=html,
        push_title="Family Calendar",
        push_body=f"Reminder: {title}",
    )


def _family_invitation(notification: Notification, user: User) -> NotificationTemplate:
    metadata = _metadata(notification)
    actor_name = _name(metadata.get("actor"), "Someone")
    body = f"{actor_name} invited you to family {_family_name(notification)}."
    text, html = _base_email(user, "Family invitation", body)
    return NotificationTemplate("Family invitation", text, html, "Family Calendar", body)


def _joined_family(notification: Notification, user: User) -> NotificationTemplate:
    body = f"You joined family {_family_name(notification)}."
    text, html = _base_email(user, "Joined family", body)
    return NotificationTemplate("Joined family", text, html, "Family Calendar", body)


def _join_request(notification: Notification, user: User) -> NotificationTemplate:
    metadata = _metadata(notification)
    status = metadata.get("status")
    actor_name = _name(metadata.get("actor"), "Someone")
    target_name = _name(metadata.get("target"), "A user")
    if status == "approved":
        body = f"{actor_name} approved your request to join family {_family_name(notification)}."
        subject = "Join request approved"
    elif status == "rejected":
        body = f"{actor_name} rejected your request to join family {_family_name(notification)}."
        subject = "Join request rejected"
    else:
        body = f"{target_name} requested to join family {_family_name(notification)}."
        subject = "Family join request"
    text, html = _base_email(user, subject, body)
    return NotificationTemplate(subject, text, html, "Family Calendar", body)


def _event_created(notification: Notification, user: User) -> NotificationTemplate:
    body = f"New event created: {_event_title(notification)}."
    text, html = _base_email(user, "New event", body)
    return NotificationTemplate("New event", text, html, "Family Calendar", body)


def _event_updated(notification: Notification, user: User) -> NotificationTemplate:
    body = f"Event updated: {_event_title(notification)}."
    text, html = _base_email(user, "Event updated", body)
    return NotificationTemplate("Event updated", text, html, "Family Calendar", body)


def _event_deleted(notification: Notification, user: User) -> NotificationTemplate:
    body = f"Event deleted: {_event_title(notification)}."
    text, html = _base_email(user, "Event deleted", body)
    return NotificationTemplate("Event deleted", text, html, "Family Calendar", body)


def _system_fallback(notification: Notification, user: User) -> NotificationTemplate:
    text, html = _base_email(user, "Family Calendar Notification", notification.message)
    return NotificationTemplate("Family Calendar Notification", text, html, "Family Calendar", notification.message)


TemplateFactory = Callable[[Notification, User], NotificationTemplate]

TEMPLATE_REGISTRY: dict[str, TemplateFactory] = {
    NotificationType.EVENT_REMINDER.value: _event_reminder,
    "event_reminder": _event_reminder,
    "family_invitation": _family_invitation,
    "joined_family": _joined_family,
    "join_request": _join_request,
    "join_request_approved": _join_request,
    "join_request_rejected": _join_request,
    "event_created": _event_created,
    "event_updated": _event_updated,
    "event_deleted": _event_deleted,
}


def resolve_template(notification: Notification, user: User) -> NotificationTemplate:
    metadata = _metadata(notification)
    template_key = metadata.get("notification_kind")
    if isinstance(template_key, str) and template_key in TEMPLATE_REGISTRY:
        return TEMPLATE_REGISTRY[template_key](notification, user)
    notification_type = notification.type.value if isinstance(notification.type, NotificationType) else str(notification.type)
    if notification_type == NotificationType.INVITE.value:
        return _family_invitation(notification, user)
    if notification_type == NotificationType.JOIN_REQUEST.value:
        return _join_request(notification, user)
    if notification.message.startswith("New event created:"):
        return _event_created(notification, user)
    if notification.message.startswith("Event updated:"):
        return _event_updated(notification, user)
    if notification.message.startswith("Event deleted:"):
        return _event_deleted(notification, user)
    factory = TEMPLATE_REGISTRY.get(notification_type, _system_fallback)
    return factory(notification, user)
