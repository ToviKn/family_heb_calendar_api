from datetime import date
from typing import Any, Callable

import pytest
from convertdate import hebrew

import services.date_service as date_service
from models.models import Event
from storage.enums import CalendarType, RepeatType


@pytest.fixture
def freeze_today(monkeypatch: pytest.MonkeyPatch) -> Callable[[date], None]:
    def _freeze(day: date) -> None:
        monkeypatch.setattr(date_service, "_today", lambda: day)

    return _freeze


def make_event(**overrides: Any) -> Event:
    payload: dict[str, Any] = {
        "title": "test",
        "month": 1,
        "day": 1,
        "family_id": 1,
        "created_by": 1,
        "calendar_type": CalendarType.GREGORIAN,
        "repeat_type": RepeatType.NONE,
        "year": 2024,
    }
    payload.update(overrides)
    return Event(**payload)


def test_none_gregorian_returns_today(freeze_today: Callable[[date], None]) -> None:
    freeze_today(date(2024, 5, 10))
    event = make_event(year=2024, month=5, day=10, repeat_type=RepeatType.NONE)

    assert date_service.calculate_next_occurrence(event) == date(2024, 5, 10)


def test_none_gregorian_returns_none_for_past(freeze_today: Callable[[date], None]) -> None:
    freeze_today(date(2024, 5, 10))
    event = make_event(year=2024, month=5, day=9, repeat_type=RepeatType.NONE)

    assert date_service.calculate_next_occurrence(event) is None


def test_yearly_handles_feb_29(freeze_today: Callable[[date], None]) -> None:
    freeze_today(date(2025, 3, 1))
    event = make_event(month=2, day=29, repeat_type=RepeatType.YEARLY, year=None)

    assert date_service.calculate_next_occurrence(event) == date(2028, 2, 29)


def test_monthly_clamps_end_of_month(freeze_today: Callable[[date], None]) -> None:
    freeze_today(date(2024, 4, 15))
    event = make_event(day=31, repeat_type=RepeatType.MONTHLY, year=None)

    assert date_service.calculate_next_occurrence(event) == date(2024, 4, 30)


def test_weekly_returns_next_weekday(freeze_today: Callable[[date], None]) -> None:
    freeze_today(date(2024, 5, 8))  # Wednesday
    event = make_event(year=2024, month=5, day=6, repeat_type=RepeatType.WEEKLY)

    assert date_service.calculate_next_occurrence(event) == date(2024, 5, 13)


def test_daily_returns_today_when_anchor_is_in_past(
    freeze_today: Callable[[date], None]
) -> None:
    freeze_today(date(2024, 5, 8))
    event = make_event(year=2024, month=5, day=6, repeat_type=RepeatType.DAILY)

    assert date_service.calculate_next_occurrence(event) == date(2024, 5, 8)


def test_none_hebrew_conversion(freeze_today: Callable[[date], None]) -> None:
    freeze_today(date(2024, 5, 8))
    h_year, h_month, h_day = hebrew.from_gregorian(2024, 5, 8)
    event = make_event(
        calendar_type=CalendarType.HEBREW,
        repeat_type=RepeatType.NONE,
        year=h_year,
        month=h_month,
        day=h_day,
    )

    assert date_service.calculate_next_occurrence(event) == date(2024, 5, 8)


def test_yearly_hebrew_returns_next_occurrence(
    freeze_today: Callable[[date], None]
) -> None:
    freeze_today(date(2024, 5, 8))
    _, h_month, h_day = hebrew.from_gregorian(2024, 5, 8)
    event = make_event(
        calendar_type=CalendarType.HEBREW,
        repeat_type=RepeatType.YEARLY,
        year=None,
        month=h_month,
        day=h_day,
    )

    assert date_service.calculate_next_occurrence(event) == date(2024, 5, 8)


def test_monthly_hebrew_returns_future_occurrence(
    freeze_today: Callable[[date], None]
) -> None:
    freeze_today(date(2024, 5, 8))
    event = make_event(
        calendar_type=CalendarType.HEBREW,
        repeat_type=RepeatType.MONTHLY,
        year=None,
        day=30,
    )

    result = date_service.calculate_next_occurrence(event)
    assert result is not None
    assert result >= date(2024, 5, 8)


def test_yearly_hebrew_adar_ii_in_non_leap_year_maps_to_adar(
    freeze_today: Callable[[date], None]
) -> None:
    freeze_today(date(2023, 1, 1))
    event = make_event(
        calendar_type=CalendarType.HEBREW,
        repeat_type=RepeatType.YEARLY,
        year=None,
        month=13,
        day=14,
    )

    result = date_service.calculate_next_occurrence(event)
    assert result is not None
    h_year, h_month, h_day = hebrew.from_gregorian(result.year, result.month, result.day)

    assert result >= date(2023, 1, 1)
    assert h_day == 14
    assert h_month in {12, 13}
