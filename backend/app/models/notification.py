from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.storage.enums import NotificationType


class NotificationCreate(BaseModel):
    event_id: int = Field(..., gt=0)


class NotificationResponse(BaseModel):
    class UserSummary(BaseModel):
        id: int
        name: str

    id: int
    user_id: int
    message: str
    metadata: dict | None = Field(default=None, alias="metadata_json")
    actor: UserSummary | None = None
    target: UserSummary | None = None
    type: NotificationType
    event_id: int | None = None
    created_at: datetime
    is_read: bool

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @field_validator("type", mode="before")
    @classmethod
    def normalize_legacy_event_reminder_type(cls, value):
        if value == "event reminder":
            return NotificationType.EVENT_REMINDER
        return value

    @model_validator(mode="after")
    def populate_actor_target_from_metadata(self) -> "NotificationResponse":
        if self.metadata is None:
            return self
        metadata = dict(self.metadata)
        actor_payload = metadata.pop("actor", metadata.pop("requested_by", None))
        target_payload = metadata.pop("target", metadata.pop("requested_user", None))
        if self.actor is None and isinstance(actor_payload, dict):
            self.actor = self.UserSummary.model_validate(actor_payload)
        if self.target is None and isinstance(target_payload, dict):
            self.target = self.UserSummary.model_validate(target_payload)
        self.metadata = metadata or None
        return self


class NotificationListResponse(BaseModel):
    events: list[NotificationResponse]
    total: int
