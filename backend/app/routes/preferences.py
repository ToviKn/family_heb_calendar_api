from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.models import User
from app.models.push import NotificationPreferencesResponse, NotificationPreferencesUpdate
from app.services.auth_service import get_current_user
from app.services.notification_preferences_service import get_or_create_preferences, update_preferences
from app.storage.database import get_db

router = APIRouter(prefix="/notification-preferences", tags=["notification-preferences"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/", response_model=NotificationPreferencesResponse)
def get_preferences(db: DbSession, current_user: CurrentUser):
    return get_or_create_preferences(db, current_user.id)


@router.put("/", response_model=NotificationPreferencesResponse)
def put_preferences(payload: NotificationPreferencesUpdate, db: DbSession, current_user: CurrentUser):
    return update_preferences(db, current_user.id, payload)
