from enum import Enum


class CalendarType(str, Enum):
    GREGORIAN = "gregorian"
    HEBREW = "hebrew"


class RepeatType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    YEARLY = "yearly"
    MONTHLY = "monthly"
    WEEKLY = "weekly"


class NotificationType(str, Enum):
    EVENT_REMINDER = "EVENT_REMINDER"
    EVENT_REMINDER_LEGACY = "event reminder"
    INVITE = "invite"
    SYSTEM = "system"
