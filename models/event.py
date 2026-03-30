import re
from datetime import date, datetime, time
from typing import Annotated, Any, cast

from convertdate import hebrew  # type: ignore[import-untyped]
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from storage.enums import CalendarType, RepeatType

field_validator_annotated = cast(Any, field_validator)
model_validator_annotated = cast(Any, model_validator)


def _validate_repeat_type_input(
    value: RepeatType | str | None,
) -> RepeatType | str | None:
    if isinstance(value, str) and value != value.lower():
        raise ValueError("repeat_type must be lowercase")
    return value


TIME_INPUT_PATTERN = re.compile(r"^\d{2}:\d{2}(?::\d{2})?$")
TIME_FIELD_DESCRIPTION = (
    "Time-only value for the event. Accepts HH:MM or HH:MM:SS and normalizes to HH:MM:SS."
)


def _time_field(example: str) -> Any:
    return Field(
        None,
        description=TIME_FIELD_DESCRIPTION,
        examples=[example],
        json_schema_extra={"example": example},
    )


def _hebrew_month_length(year: int, month: int) -> int:
    month_length = cast(Any, getattr(hebrew, "month_length"))
    return cast(int, month_length(year, month))


def _parse_time_only(value: time | str | None) -> time | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        raise ValueError("time fields must use HH:MM or HH:MM:SS format, not datetime")

    if isinstance(value, time):
        if value.tzinfo is not None:
            raise ValueError("time fields must not include a timezone")
        return value.replace(microsecond=0)

    if isinstance(value, str):
        if "T" in value or " " in value:
            raise ValueError("time fields must use HH:MM or HH:MM:SS format, not datetime")
        if not TIME_INPUT_PATTERN.fullmatch(value):
            raise ValueError("time fields must use HH:MM or HH:MM:SS format")
        try:
            parsed_value = time.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("time fields must use HH:MM or HH:MM:SS format") from exc
        if parsed_value.tzinfo is not None:
            raise ValueError("time fields must not include a timezone")
        return parsed_value.replace(microsecond=0)

    raise ValueError("time fields must use HH:MM or HH:MM:SS format")


RequestRepeatType = Annotated[
    RepeatType,
    BeforeValidator(_validate_repeat_type_input),
]


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    calendar_type: CalendarType = CalendarType.GREGORIAN
    year: int | None = Field(None, ge=1)
    month: int = Field(..., ge=1, le=13)
    day: int = Field(..., ge=1, le=31)
    repeat_type: RepeatType = RepeatType.NONE
    family_id: int = Field(..., gt=0)
    created_by: int = Field(..., gt=0)
    start_time: time | None = _time_field("18:00:00")
    end_time: time | None = _time_field("20:00:00")

    @field_validator_annotated("start_time", "end_time", mode="before")  # type: ignore[misc]
    @classmethod
    def validate_time_only(cls, value: time | str | None) -> time | None:
        return _parse_time_only(value)

    @field_validator_annotated("end_time")  # type: ignore[misc]
    @classmethod
    def validate_end_time(
        cls, value: time | None, info: ValidationInfo
    ) -> time | None:
        start_time = info.data.get("start_time")
        if value is not None and isinstance(start_time, time) and value <= start_time:
            raise ValueError("end_time must be after start_time")
        return value

    @model_validator_annotated(mode="after")
    def validate_event_date(self) -> Self:
        if self.year == 1 and self.month == 1 and self.day == 1:
            raise ValueError("placeholder date 0001-01-01 is not allowed")

        if self.repeat_type == RepeatType.NONE and self.year is None:
            raise ValueError("year is required for non-recurring events")

        validation_year = self.year
        if validation_year is None:
            validation_year = date.today().year

        if self.calendar_type == CalendarType.GREGORIAN:
            try:
                date(validation_year, self.month, self.day)
            except ValueError as exc:
                raise ValueError(f"invalid Gregorian date: {exc}") from exc
        else:
            if validation_year < 1:
                raise ValueError("Hebrew year must be positive")
            if self.month == 13 and not hebrew.leap(validation_year):
                raise ValueError("invalid Hebrew month 13 in non-leap year")
            max_day = _hebrew_month_length(validation_year, self.month)
            if self.day > max_day:
                raise ValueError(
                    f"day must be between 1 and {max_day} for Hebrew month {self.month}"
                )

        return self


class EventCreate(EventBase):
    repeat_type: RequestRepeatType = RepeatType.NONE


class EventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    year: int | None = Field(None, ge=1)
    month: int | None = Field(None, ge=1, le=13)
    day: int | None = Field(None, ge=1, le=31)
    repeat_type: RequestRepeatType | None = None
    start_time: time | None = _time_field("18:00:00")
    end_time: time | None = _time_field("20:00:00")

    @field_validator_annotated("start_time", "end_time", mode="before")  # type: ignore[misc]
    @classmethod
    def validate_time_only(cls, value: time | str | None) -> time | None:
        return _parse_time_only(value)

    @field_validator_annotated("end_time")  # type: ignore[misc]
    @classmethod
    def validate_end_time(
        cls, value: time | None, info: ValidationInfo
    ) -> time | None:
        start_time = info.data.get("start_time")
        if value is not None and isinstance(start_time, time) and value <= start_time:
            raise ValueError("end_time must be after start_time")
        return value


class EventResponse(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime
    next_occurrence: date | None = None

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    events: list[EventResponse]
    total: int
    page: int | None = None
    per_page: int | None = None


class SimpleDate(BaseModel):
    year: int = Field(..., title="Year")
    month: int = Field(..., title="Month")
    day: int = Field(..., title="Day")

    model_config = {
        "json_schema_extra": {
            "example": {
                "year": 2026,
                "month": 3,
                "day": 26
            }
        }
    }

class DateConversionResponse(BaseModel):
    gregorian_date: SimpleDate
    hebrew_date: SimpleDate

    model_config = {
        "json_schema_extra": {
            "example": {
                "gregorian_date": {"year": 2026, "month": 3, "day": 26},
                "hebrew_date": {"year": 5786, "month": 1, "day": 8}
            }
        }
    }

class ErrorResponse(BaseModel):
    message: str
    details: dict[str, str] | None = None
