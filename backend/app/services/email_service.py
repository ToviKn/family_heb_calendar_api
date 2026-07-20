import logging
import smtplib
from email.message import EmailMessage
from html import escape

from app.config import settings
from app.models.models import Notification, User

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    if settings.email_provider.lower() != "smtp":
        logger.info("Email skipped: provider disabled", extra={"operation": "send_email"})
        return False
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.email_from]):
        logger.warning("Email skipped: SMTP configuration incomplete", extra={"operation": "send_email"})
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from
    message["To"] = to_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        logger.info("Email sent", extra={"operation": "send_email", "to_email": to_email})
        return True
    except Exception:
        logger.error("Email failed", exc_info=True, extra={"operation": "send_email", "to_email": to_email})
        return False


def send_event_reminder(user: User, notification: Notification) -> bool:
    title = (notification.metadata_json or {}).get("event_title") or notification.message
    first_name = user.name.split()[0] if user.name else "there"
    text = f"Hello {first_name}\n\nThis is a reminder that:\n\n{title}\n\noccurs today.\n\nOpen the application to view details."
    html = f"<p>Hello {escape(first_name)}</p><p>This is a reminder that:</p><p><strong>{escape(str(title))}</strong></p><p>occurs today.</p><p>Open the application to view details.</p>"
    return send_email(user.email, "Family Calendar Reminder", text, html)
