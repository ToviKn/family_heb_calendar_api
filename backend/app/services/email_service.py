import logging
import smtplib
from email.message import EmailMessage

import requests

from app.config import settings
from app.models.models import Notification, User

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    """
        Send email using the configured provider.
        Supported providers:
            smtp
            resend
        """
    provider = settings.email_provider.lower()
    if provider == "smtp":
        return send_email_smtp(to_email, subject, text_body, html_body,)
    if provider == "resend":
        return send_email_resend(to_email, subject, text_body, html_body,)

    logger.warning("Unknown email provider", extra={"operation": "send_email", "provider": provider,})
    return False

def send_email_smtp(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.email_from]):
        logger.warning("SMTP configuration incomplete", extra={"operation": "send_email"})
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from
    message["To"] = to_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        logger.info("Email sent via SMTP", extra={"operation": "send_email", "to_email": to_email})
        return True
    except Exception:
        logger.exception("SMTP send failed", extra={"operation": "send_email", "to_email": to_email})
        return False

def send_email_resend(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    if not settings.resend_api_key:
        logger.warning("Missing Resend API key", extra={"operation": "send_email"})
        return False

    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "from": settings.email_from,
        "to": [to_email],
        "subject": subject,
        "text": text_body,
        "html": html_body,
    }

    try:
        response = requests.post(settings.resend_api_url, headers=headers, json=payload, timeout=15,)
        response.raise_for_status()
        logger.info("Email sent via Resend",extra={"operation": "send_email_resend", "to_email": to_email,},)
        return True

    except requests.RequestException:
        logger.exception("Resend HTTP error", extra={"operation": "send_email_resend", "status_code": response.status_code, "response": response.text, "to_email": to_email})
        return False

    except Exception:
        logger.exception("Resend send failed", extra={"operation": "send_email", "to_email": to_email})
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
