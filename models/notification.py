from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from storage.enums import NotificationType


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



class NotificationListResponse(BaseModel):
    events: list[NotificationResponse]
    total: int
