import logging
from calendar import monthrange
from datetime import date, timedelta

from convertdate import hebrew

from exceptions import DateConversionError, ValidationError
from models.models import Event
from storage.enums import CalendarType, RepeatType
from models.event import DateConversionResponse, SimpleDate

logger = logging.getLogger(__name__)


def hebrew_month_length(year: int, month: int) -> int:
    return int(hebrew.month_days(year, month))


def validate_gregorian_date(year: int, month: int, day: int) -> None:
    """Validate Gregorian date and raise ValidationError if invalid."""
    logger.debug(
        "Validating Gregorian date", extra={"year": year, "month": month, "day": day}
    )

    if year < 1 or year > 9999:
        raise ValidationError("Year must be between 1 and 9999", "year")

    if month < 1 or month > 12:
        raise ValidationError("Month must be between 1 and 12", "month")

    if day < 1 or day > 31:
        raise ValidationError("Day must be between 1 and 31", "day")

    try:
        date(year, month, day)
    except ValueError as exc:
        logger.warning(
            "Invalid Gregorian date",
            extra={"year": year, "month": month, "day": day, "error": str(exc)},
        )
        raise ValidationError(f"Invalid Gregorian date: {exc}", "date") from exc


def validate_hebrew_date(year: int, month: int, day: int) -> None:
    """Validate Hebrew date and raise ValidationError if invalid."""
    logger.debug(
        "Validating Hebrew date", extra={"year": year, "month": month, "day": day}
    )

    if year < 1:
        raise ValidationError("Hebrew year must be positive", "year")

    if month < 1 or month > 13:
        raise ValidationError("Hebrew month must be between 1 and 13", "month")

    if month == 13 and not hebrew.leap(year):
        logger.warning("Month 13 in non-leap Hebrew year", extra={"year": year})
        raise ValidationError("Invalid Hebrew month 13 in non-leap year", "month")

    try:
        max_day = hebrew_month_length(year, month)
    except Exception as exc:
        logger.warning(
            "Invalid Hebrew date structure",
            extra={"year": year, "month": month, "day": day, "error": str(exc)},
        )
        raise ValidationError(f"Invalid Hebrew date: {exc}", "date") from exc

    if day < 1 or day > max_day:
        raise ValidationError(
            f"Day must be between 1 and {max_day} for Hebrew month {month}", "day"
        )


def convert_to_hebrew(year: int, month: int, day: int) -> tuple[int, int, int]:
    """Convert Gregorian date to Hebrew date."""
    logger.info(
        "Converting Gregorian to Hebrew",
        extra={"year": year, "month": month, "day": day},
    )

    try:
        validate_gregorian_date(year, month, day)
        result = hebrew.from_gregorian(year, month, day)
        logger.info("Conversion result", extra={"result": result})
        return result
    except ValidationError:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error in Gregorian to Hebrew conversion", exc_info=True
        )
        raise DateConversionError(
            f"Failed to convert Gregorian to Hebrew: {exc}",
            "gregorian",
            {"year": year, "month": month, "day": day},
        ) from exc


def convert_to_gregorian(year: int, month: int, day: int) -> tuple[int, int, int]:
    """Convert Hebrew date to Gregorian date."""
    logger.info(
        "Converting Hebrew to Gregorian",
        extra={"year": year, "month": month, "day": day},
    )

    try:
        validate_hebrew_date(year, month, day)
        result = hebrew.to_gregorian(year, month, day)
        logger.info("Conversion result", extra={"result": result})
        return result
    except ValidationError:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error in Hebrew to Gregorian conversion", exc_info=True
        )
        raise DateConversionError(
            f"Failed to convert Hebrew to Gregorian: {exc}",
            "hebrew",
            {"year": year, "month": month, "day": day},
        ) from exc


def _today() -> date:
    return date.today()


def _resolve_hebrew_month_for_year(source_month: int, target_h_year: int) -> int:
    """Resolve Adar handling when translating a month into a target Hebrew year."""
    if source_month == 13 and not hebrew.leap(target_h_year):
        logger.debug(
            "Mapping Hebrew Adar II to Adar in non-leap year",
            extra={"source_month": source_month, "target_h_year": target_h_year},
        )
        return 12
    return source_month


def _gregorian_for_hebrew(h_year: int, h_month: int, h_day: int) -> date:
    normalized_month = _resolve_hebrew_month_for_year(h_month, h_year)
    max_day = hebrew_month_length(h_year, normalized_month)
    candidate_day = min(h_day, max_day)
    g_year, g_month, g_day = convert_to_gregorian(h_year, normalized_month, candidate_day)
    return date(g_year, g_month, g_day)


def _next_yearly_gregorian(month: int, day: int, today: date) -> date:
    if month == 2 and day == 29:
        year = today.year
        while True:
            is_leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
            if is_leap:
                candidate = date(year, 2, 29)
                if candidate >= today:
                    return candidate
            year += 1

    candidate = date(today.year, month, day)
    if candidate < today:
        candidate = date(today.year + 1, month, day)
    return candidate


def _next_monthly_gregorian(day: int, today: date) -> date:
    year = today.year
    month = today.month

    for _ in range(24):
        last_day = monthrange(year, month)[1]
        candidate = date(year, month, min(day, last_day))
        if candidate >= today:
            return candidate

        month += 1
        if month > 12:
            month = 1
            year += 1

    raise ValidationError("Unable to determine next monthly occurrence", "repeat_type")


def _next_weekly(weekday: int, today: date) -> date:
    delta = (weekday - today.weekday()) % 7
    return today + timedelta(days=delta)


def _advance_hebrew_month(h_year: int, h_month: int) -> tuple[int, int]:
    months_in_year = 13 if hebrew.leap(h_year) else 12
    if h_month < months_in_year:
        return h_year, h_month + 1
    return h_year + 1, 1


def _next_yearly_hebrew(month: int, day: int, today: date) -> date:
    today_h_year, _, _ = convert_to_hebrew(today.year, today.month, today.day)
    for h_year in range(today_h_year, today_h_year + 4):
        candidate = _gregorian_for_hebrew(h_year, month, day)
        if candidate >= today:
            return candidate
    raise ValidationError("Unable to determine next yearly Hebrew occurrence", "date")


def _next_monthly_hebrew(day: int, today: date) -> date:
    h_year, h_month, _ = convert_to_hebrew(today.year, today.month, today.day)
    current_year = h_year
    current_month = h_month

    for _ in range(30):
        max_day = hebrew_month_length(current_year, current_month)
        candidate = _gregorian_for_hebrew(current_year, current_month, min(day, max_day))
        if candidate >= today:
            return candidate
        current_year, current_month = _advance_hebrew_month(current_year, current_month)

    raise ValidationError("Unable to determine next monthly Hebrew occurrence", "date")


def hebrew_to_gregorian_next(month: int, day: int) -> date:
    """Get the next occurrence of a Hebrew month/day in Gregorian calendar."""
    try:
        return _next_yearly_hebrew(month, day, _today())
    except ValidationError:
        raise
    except Exception as exc:
        logger.error("Failed to calculate next Hebrew date occurrence", exc_info=True)
        raise DateConversionError(
            f"Failed to calculate next occurrence: {exc}",
            "hebrew_next",
            {"month": month, "day": day},
        ) from exc


def calculate_next_occurrence(
    event: Event, reference_date: date | None = None
) -> date | None:
    """Return the next future event occurrence on or after today.

    Supports Gregorian and Hebrew calendar events with NONE, DAILY, YEARLY,
    MONTHLY, and WEEKLY recurrences. Hebrew events are converted to Gregorian
    dates for comparison and scheduling. Monthly recurrences clamp to
    end-of-month when the source day does not exist in the target month.

    Raises:
        ValidationError: If required event fields are missing or invalid.
        DateConversionError: If Hebrew/Gregorian conversion fails unexpectedly.
    """
    today = reference_date or _today()
    logger.info(
        "Calculating next occurrence",
        extra={
            "event_id": event.id,
            "calendar_type": str(event.calendar_type),
            "repeat_type": event.repeat_type,
            "year": event.year,
            "month": event.month,
            "day": event.day,
            "today": today.isoformat(),
        },
    )

    if event.month is None or event.day is None:
        logger.warning(
            "Missing event month/day while calculating next occurrence",
            extra={"event_id": event.id, "month": event.month, "day": event.day},
        )
        raise ValidationError("Event month and day are required", "date")

    event_month = event.month
    event_day = event.day

    # One-time events
    if event.repeat_type == RepeatType.NONE:
        if event.year is None:
            raise ValidationError("One-time events require a year", "year")
        event_year = event.year

        if event.calendar_type == CalendarType.GREGORIAN:
            validate_gregorian_date(event_year, event_month, event_day)
            occurrence = date(event_year, event_month, event_day)
        elif event.calendar_type == CalendarType.HEBREW:
            occurrence = _gregorian_for_hebrew(event_year, event_month, event_day)
        else:
            raise ValidationError(
                f"Unsupported calendar type: {event.calendar_type}", "calendar_type"
            )

        if occurrence >= today:
            logger.debug(
                "Resolved one-time occurrence",
                extra={"event_id": event.id, "occurrence": occurrence.isoformat()},
            )
            return occurrence
        logger.debug(
            "One-time occurrence is in the past",
            extra={"event_id": event.id, "occurrence": occurrence.isoformat()},
        )
        return None

    if event.repeat_type == RepeatType.DAILY:
        if event.year is None:
            raise ValidationError("Daily events require a year anchor", "year")
        event_year = event.year

        if event.calendar_type == CalendarType.GREGORIAN:
            validate_gregorian_date(event_year, event_month, event_day)
            anchor = date(event_year, event_month, event_day)
        elif event.calendar_type == CalendarType.HEBREW:
            anchor = _gregorian_for_hebrew(event_year, event_month, event_day)
        else:
            raise ValidationError(
                f"Unsupported calendar type: {event.calendar_type}", "calendar_type"
            )

        occurrence = max(anchor, today)
        logger.debug(
            "Resolved daily occurrence",
            extra={
                "event_id": event.id,
                "anchor": anchor.isoformat(),
                "occurrence": occurrence.isoformat(),
            },
        )
        return occurrence

    # Weekly events rely on the weekday of a concrete anchor date.
    if event.repeat_type == RepeatType.WEEKLY:
        if event.year is None:
            raise ValidationError("Weekly events require a year anchor", "year")
        event_year = event.year

        if event.calendar_type == CalendarType.GREGORIAN:
            validate_gregorian_date(event_year, event_month, event_day)
            anchor = date(event_year, event_month, event_day)
        elif event.calendar_type == CalendarType.HEBREW:
            anchor = _gregorian_for_hebrew(event_year, event_month, event_day)
        else:
            raise ValidationError(
                f"Unsupported calendar type: {event.calendar_type}", "calendar_type"
            )

        occurrence = _next_weekly(anchor.weekday(), today)
        logger.debug(
            "Resolved weekly occurrence",
            extra={
                "event_id": event.id,
                "anchor_weekday": anchor.weekday(),
                "occurrence": occurrence.isoformat(),
            },
        )
        return occurrence

    if event.calendar_type == CalendarType.HEBREW:
        if event.repeat_type == RepeatType.YEARLY:
            occurrence = _next_yearly_hebrew(event_month, event_day, today)
            logger.debug(
                "Resolved yearly Hebrew occurrence",
                extra={"event_id": event.id, "occurrence": occurrence.isoformat()},
            )
            return occurrence
        if event.repeat_type == RepeatType.MONTHLY:
            occurrence = _next_monthly_hebrew(event_day, today)
            logger.debug(
                "Resolved monthly Hebrew occurrence",
                extra={"event_id": event.id, "occurrence": occurrence.isoformat()},
            )
            return occurrence
        raise ValidationError(
            f"Unsupported repeat type for Hebrew calendar: {event.repeat_type}",
            "repeat_type",
        )

    if event.calendar_type == CalendarType.GREGORIAN:
        if event.repeat_type == RepeatType.YEARLY:
            validate_gregorian_date(
                2024 if event_month == 2 else today.year, event_month, event_day
            )
            occurrence = _next_yearly_gregorian(event_month, event_day, today)
            logger.debug(
                "Resolved yearly Gregorian occurrence",
                extra={"event_id": event.id, "occurrence": occurrence.isoformat()},
            )
            return occurrence
        if event.repeat_type == RepeatType.MONTHLY:
            if event_day < 1 or event_day > 31:
                raise ValidationError("Day must be between 1 and 31", "day")
            occurrence = _next_monthly_gregorian(event_day, today)
            logger.debug(
                "Resolved monthly Gregorian occurrence",
                extra={"event_id": event.id, "occurrence": occurrence.isoformat()},
            )
            return occurrence
        raise ValidationError(
            f"Unsupported repeat type for Gregorian calendar: {event.repeat_type}",
            "repeat_type",
        )

    raise ValidationError(f"Unsupported calendar type: {event.calendar_type}", "calendar_type")


def get_today_dates() -> DateConversionResponse:
    """Get today's date in both Gregorian and Hebrew formats."""
    try:
        today = date.today()
        h_year, h_month, h_day = convert_to_hebrew(today.year, today.month, today.day)

        return DateConversionResponse(
            gregorian_date=SimpleDate(year=today.year, month=today.month, day=today.day),
            hebrew_date=SimpleDate(year=h_year, month=h_month, day=h_day),
        )

    except Exception as exc:
        logger.error("Failed to get today's dates", exc_info=True)
        raise DateConversionError(
            f"Failed to get today's dates: {exc}", "today", {}
        ) from exc
