import logging
import smtplib
from email.message import EmailMessage

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
    from app.services.notification_templates import resolve_template

    template = resolve_template(notification, user)
    return send_email(
        user.email,
        template.email_subject,
        template.email_text_body,
        template.email_html_body,
    )
