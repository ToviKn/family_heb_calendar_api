from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PushKeys(BaseModel):
    p256dh: str = Field(..., min_length=1, max_length=512)
    auth: str = Field(..., min_length=1, max_length=512)


class PushSubscriptionCreate(BaseModel):
    endpoint: str = Field(..., min_length=10, max_length=2048)
    keys: PushKeys

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        if not value.startswith(("https://", "http://localhost")):
            raise ValueError("Endpoint must be HTTPS")
        return value


class PushUnsubscribeRequest(BaseModel):
    endpoint: str = Field(..., min_length=10, max_length=2048)


class PushSubscriptionResponse(BaseModel):
    id: int
    user_id: int
    endpoint: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: bool | None = None
    push_enabled: bool | None = None
    notify_today: bool | None = None
    notify_day_before: bool | None = None


class NotificationPreferencesResponse(BaseModel):
    user_id: int
    email_enabled: bool
    push_enabled: bool
    notify_today: bool
    notify_day_before: bool

    model_config = ConfigDict(from_attributes=True)
