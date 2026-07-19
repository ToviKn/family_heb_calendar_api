from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Index, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.database import Base
from app.storage.enums import CalendarType, NotificationType, RepeatType


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    memberships: Mapped[list[FamilyMembership]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    events_created: Mapped[list[Event]] = relationship(back_populates="creator")
    notifications: Mapped[list[Notification]] = relationship(back_populates="user")
    push_subscriptions: Mapped[list[PushSubscription]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notification_preferences: Mapped[UserNotificationPreferences | None] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class Family(Base):
    __tablename__ = "families"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    members: Mapped[list[FamilyMembership]] = relationship(
        back_populates="family", cascade="all, delete-orphan"
    )
    events: Mapped[list[Event]] = relationship(
        back_populates="family", cascade="all, delete-orphan"
    )


class FamilyMembership(Base):
    __tablename__ = "family_memberships"
    __table_args__ = (UniqueConstraint("user_id", "family_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="member")
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="memberships")
    family: Mapped[Family] = relationship(back_populates="members")

    @property
    def family_name(self) -> str | None:
        return self.family.name if self.family is not None else None


class FamilyJoinRequest(Base):
    __tablename__ = "family_join_requests"
    __table_args__ = (
        UniqueConstraint("user_id", "family_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), nullable=False)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    year: Mapped[int | None] = mapped_column(nullable=True)
    month: Mapped[int] = mapped_column(nullable=False)
    day: Mapped[int] = mapped_column(nullable=False)

    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    calendar_type: Mapped[str] = mapped_column(
        String(50), default=CalendarType.GREGORIAN.value, nullable=False
    )
    repeat_type: Mapped[str] = mapped_column(
        String(50), default=RepeatType.NONE.value, nullable=False
    )
    next_occurrence: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    family: Mapped[Family] = relationship(back_populates="events")
    creator: Mapped[User] = relationship(back_populates="events_created")
    participants: Mapped[list[EventParticipant]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    notifications: Mapped[list[Notification]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

    @property
    def family_name(self) -> str | None:
        return self.family.name if self.family is not None else None


class EventParticipant(Base):
    __tablename__ = "event_participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="invited")
    invited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    event: Mapped[Event] = relationship(back_populates="participants")
    user: Mapped[User] = relationship()


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_event_type", "user_id", "event_id", "type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    type: Mapped[NotificationType] = mapped_column(
        String(50), default=NotificationType.SYSTEM.value
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    send_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="notifications")
    event: Mapped[Event | None] = relationship(back_populates="notifications")

    @property
    def family_id(self) -> int | None:
        return self.event.family_id if self.event is not None else None

    @property
    def family_name(self) -> str | None:
        return self.event.family.name if self.event is not None and self.event.family is not None else None


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "endpoint"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    p256dh_key: Mapped[str] = mapped_column(String(512), nullable=False)
    auth_key: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="push_subscriptions")


class UserNotificationPreferences(Base):
    __tablename__ = "user_notification_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_today: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_day_before: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped[User] = relationship(back_populates="notification_preferences")
