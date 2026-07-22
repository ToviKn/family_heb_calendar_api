from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Callable

from app.config import settings
from app.locales import translate
from app.models.models import Notification, User
from app.storage.enums import NotificationType
from app.utils.localization import (
    format_date,
    translate_repeat_type,
)


@dataclass(frozen=True)
class NotificationTemplate:
    email_subject: str
    email_text_body: str
    email_html_body: str
    push_title: str
    push_body: str
    push_url: str = "/notifications"


@dataclass(frozen=True)
class ReminderField:
    label: str
    value: str


@dataclass(frozen=True)
class ReminderEmailData:
    language: str
    subject: str
    greeting: str
    heading: str
    intro: str
    fields: tuple[ReminderField, ...]
    action_label: str
    action_url: str
    footer: str


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


def _language(user: User) -> str:
    return user.language if user.language in {"en", "he"} else "en"


def _first_name(user: User) -> str:
    return user.name.split()[0] if user.name else translate(_language(user), "there")


def _string_value(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _time_value(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value[:5]


def _calendar_type_key(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.lower().removeprefix("calendartype.")
    if normalized in {"gregorian", "hebrew"}:
        return normalized
    return None


def _reminder_timing_key(reminder_type: object) -> str:
    return reminder_type if reminder_type in {"today", "tomorrow"} else "future"


def _app_url(path: str) -> str:
    return f"{settings.app_url.rstrip('/')}/{path.lstrip('/')}"


def _build_reminder_data(notification: Notification, user: User) -> tuple[ReminderEmailData, str, str]:
    metadata = _metadata(notification)
    language = _language(user)
    title = _event_title(notification)
    reminder_timing = _reminder_timing_key(metadata.get("reminder_type"))
    calendar_type_key = _calendar_type_key(metadata.get("calendar_type"))
    fields: list[ReminderField] = []

    reminder_for = translate(language, reminder_timing)
    if reminder_timing in {"today", "tomorrow"}:
        fields.append(ReminderField(translate(language, "reminder_for"), reminder_for))

    field_candidates = [
        ("event", title),
        ("description", _string_value(metadata.get("event_description"))),
        ("date", format_date(_string_value(metadata.get("date")), language)),
        ("hebrew_date", _string_value(metadata.get("formatted_hebrew_date")) if calendar_type_key == "hebrew" else None),
        ("start_time", _time_value(metadata.get("start_time"))),
        ("end_time", _time_value(metadata.get("end_time"))),
        ("family", _string_value(metadata.get("family_name"))),
        ("repeat", translate_repeat_type(_string_value(metadata.get("repeat_type")), language)),
        (
            "calendar_type",
            translate(language, f"calendar_type_{calendar_type_key}") if calendar_type_key else None,
        ),
    ]

    for label_key, value in field_candidates:
        if value:
            fields.append(ReminderField(translate(language, label_key), value))

    subject_key = f"event_reminder_subject_{reminder_timing}"
    subject = translate(language, subject_key).format(title=title)

    data = ReminderEmailData(
        language=language,
        subject=subject,
        greeting=translate(language, "hello_name").format(name=_first_name(user)),
        heading=translate(language, "event_reminder_subject"),
        intro=translate(language, f"reminder_{reminder_timing}"),
        fields=tuple(fields),
        action_label=translate(language, "open"),
        action_url=_app_url("/notifications"),
        footer=translate(language, "open_details"),
    )
    push_title = translate(language, "push_title")
    push_body = translate(language, f"push_{reminder_timing}").format(title=title)
    return data, push_title, push_body


def _render_reminder_text(data: ReminderEmailData) -> str:
    lines = [
        data.greeting,
        "",
        data.intro,
        "",
        *[f"{field.label}: {field.value}" for field in data.fields],
        "",
        f"{data.action_label}: {data.action_url}",
        data.footer,
    ]
    return "\n".join(lines)


def _render_reminder_html(data: ReminderEmailData) -> str:
    direction = "rtl" if data.language == "he" else "ltr"
    text_align = "right" if data.language == "he" else "left"
    rows = "".join(
        "<tr>"
        f'<td style="padding:10px 0;color:#64748b;font-size:13px;width:38%;vertical-align:top;">{escape(field.label)}</td>'
        f'<td style="padding:10px 0;color:#0f172a;font-size:15px;font-weight:600;vertical-align:top;">{escape(field.value)}</td>'
        "</tr>"
        for field in data.fields
    )
    return f"""<!doctype html>
<html lang="{escape(data.language)}" dir="{direction}">
  <body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,Helvetica,sans-serif;color:#0f172a;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f8fafc;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;">
            <tr>
              <td style="padding:28px 28px 18px;text-align:{text_align};">
                <div style="display:inline-block;padding:6px 10px;border-radius:999px;background:#dbeafe;color:#1d4ed8;font-size:12px;font-weight:700;">{escape(data.heading)}</div>
                <h1 style="margin:18px 0 8px;font-size:24px;line-height:1.25;color:#0f172a;">{escape(data.greeting)}</h1>
                <p style="margin:0;color:#475569;font-size:16px;line-height:1.55;">{escape(data.intro)}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px;text-align:{text_align};">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-top:1px solid #e2e8f0;border-bottom:1px solid #e2e8f0;">
                  {rows}
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 30px;text-align:{text_align};">
                <a href="{escape(data.action_url)}" style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;border-radius:10px;padding:12px 18px;font-size:15px;font-weight:700;">{escape(data.action_label)}</a>
                <p style="margin:16px 0 0;color:#64748b;font-size:13px;line-height:1.5;">{escape(data.footer)}</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _event_reminder(notification: Notification, user: User) -> NotificationTemplate:
    data, push_title, push_body = _build_reminder_data(notification, user)

    return NotificationTemplate(
        email_subject=data.subject,
        email_text_body=_render_reminder_text(data),
        email_html_body=_render_reminder_html(data),
        push_title=push_title,
        push_body=push_body,
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
