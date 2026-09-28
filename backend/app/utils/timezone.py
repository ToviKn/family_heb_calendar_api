"""Application-local clock helpers used for calendar-date decisions."""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.config import settings


def application_today(now: datetime | None = None) -> date:
    """Return today's calendar date in the configured application timezone.

    Events are date-based, so this deliberately does not compare an event's
    optional start time with the current time.
    """
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        raise ValueError("application_today requires a timezone-aware datetime")
    return current_time.astimezone(ZoneInfo(settings.app_timezone)).date()
