from sqlalchemy.orm import Session

from app.models.models import UserNotificationPreferences
from app.models.push import NotificationPreferencesUpdate


def get_or_create_preferences(db: Session, user_id: int) -> UserNotificationPreferences:
    preferences = db.get(UserNotificationPreferences, user_id)
    if preferences is None:
        preferences = UserNotificationPreferences(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    return preferences


def update_preferences(db: Session, user_id: int, payload: NotificationPreferencesUpdate) -> UserNotificationPreferences:
    preferences = get_or_create_preferences(db, user_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    db.commit()
    db.refresh(preferences)
    return preferences
