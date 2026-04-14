import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from exceptions import CalendarAPIException
from models.models import User
from models.notification import NotificationCreate, NotificationResponse
from services import notification_service
from services.auth_service import get_current_user
from storage.database import get_db

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _as_http(exc: CalendarAPIException) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/", response_model=NotificationResponse, status_code=201)
def create_notification(payload: NotificationCreate, db: DbSession, current_user: CurrentUser) -> NotificationResponse:
    try:
        return notification_service.create_notification(db, payload, current_user.id)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.get("/", response_model=list[NotificationResponse])
def get_notifications(db: DbSession, current_user: CurrentUser) -> list[NotificationResponse]:
    try:
        return notification_service.get_user_notifications(db, current_user.id)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(notification_id: int, db: DbSession, current_user: CurrentUser) -> NotificationResponse:
    try:
        return notification_service.mark_notification_as_read(db, notification_id, current_user.id)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.delete("/{notification_id}", status_code=204)
def delete_notification(notification_id: int, db: DbSession, current_user: CurrentUser) -> None:
    try:
        notification_service.delete_notification(db, notification_id, current_user.id)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.post("/reminders/process")
def process_reminders(db: DbSession, _: CurrentUser) -> dict[str, int]:
    try:
        created = notification_service.process_event_reminders(db)
        return {"created": created}
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc
