from typing import Any

from fastapi import status


class CalendarAPIException(Exception):
    """Base exception for calendar API."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(CalendarAPIException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        details = {"field": field} if field else {}
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class NotFoundError(CalendarAPIException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: Any) -> None:
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class DatabaseError(CalendarAPIException):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: str | None = None) -> None:
        details = {"operation": operation} if operation else {}
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class DateConversionError(CalendarAPIException):
    """Raised when date conversion fails."""

    def __init__(
        self, message: str, calendar_type: str, date_values: dict[str, int]
    ) -> None:
        details = {"calendar_type": calendar_type, "date_values": date_values}
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)
