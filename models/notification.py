from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

NotificationType = Literal["event reminder", "invite", "system", "EVENT_REMINDER"]


class NotificationCreate(BaseModel):
    event_id: int = Field(..., gt=0)


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    type: NotificationType
    event_id: int | None = None
    created_at: datetime
    is_read: bool

    model_config = ConfigDict(from_attributes=True)
