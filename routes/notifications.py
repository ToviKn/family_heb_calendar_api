import logging
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.models import User
from models.notification import NotificationCreate, NotificationResponse
from services.auth_service import get_current_user
from services import notification_service
from storage.database import get_db

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/", response_model=NotificationResponse, status_code=201)
def create_notification(
    payload: NotificationCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> NotificationResponse:
    logger.info(
        "Create notification request started",
        extra={"operation": "create_notification", "user_id": current_user.id},
    )
    try:
        notification = cast(
            NotificationResponse,
            notification_service.create_notification(db, payload, current_user.id),
        )
        logger.info(
            "Create notification request completed",
            extra={
                "operation": "create_notification",
                "user_id": current_user.id,
                "notification_id": notification.id,
            },
        )
        return notification
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Create notification request failed",
            exc_info=True,
            extra={"operation": "create_notification", "user_id": current_user.id},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/", response_model=list[NotificationResponse])
def get_notifications(db: DbSession, current_user: CurrentUser) -> list[NotificationResponse]:
    logger.info(
        "Get notifications request started",
        extra={"operation": "get_notifications", "user_id": current_user.id},
    )
    try:
        notifications = cast(
            list[NotificationResponse],
            notification_service.get_user_notifications(db, current_user.id),
        )
        logger.info(
            "Get notifications request completed",
            extra={
                "operation": "get_notifications",
                "user_id": current_user.id,
                "result_count": len(notifications),
            },
        )
        return notifications
    except Exception as exc:
        logger.error(
            "Get notifications request failed",
            exc_info=True,
            extra={"operation": "get_notifications", "user_id": current_user.id},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> NotificationResponse:
    logger.info(
        "Mark notification as read request started",
        extra={
            "operation": "mark_notification_read",
            "user_id": current_user.id,
            "notification_id": notification_id,
        },
    )
    try:
        notification = cast(
            NotificationResponse,
            notification_service.mark_notification_as_read(db, notification_id, current_user.id),
        )
        logger.info(
            "Mark notification as read request completed",
            extra={
                "operation": "mark_notification_read",
                "user_id": current_user.id,
                "notification_id": notification.id,
            },
        )
        return notification
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Mark notification as read request failed",
            exc_info=True,
            extra={
                "operation": "mark_notification_read",
                "user_id": current_user.id,
                "notification_id": notification_id,
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/{notification_id}", status_code=204)
def delete_notification(
    notification_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    logger.info(
        "Delete notification request started",
        extra={
            "operation": "delete_notification",
            "user_id": current_user.id,
            "notification_id": notification_id,
        },
    )
    try:
        notification_service.delete_notification(db, notification_id, current_user.id)
        logger.info(
            "Delete notification request completed",
            extra={
                "operation": "delete_notification",
                "user_id": current_user.id,
                "notification_id": notification_id,
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Delete notification request failed",
            exc_info=True,
            extra={
                "operation": "delete_notification",
                "user_id": current_user.id,
                "notification_id": notification_id,
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/reminders/process")
def process_reminders(db: DbSession, _: CurrentUser) -> dict[str, int]:
    logger.info("Process reminders request started", extra={"operation": "process_reminders"})
    try:
        created = notification_service.process_event_reminders(db)
        logger.info(
            "Process reminders request completed",
            extra={"operation": "process_reminders", "created_count": created},
        )
        return {"created": created}
    except Exception as exc:
        logger.error(
            "Process reminders request failed",
            exc_info=True,
            extra={"operation": "process_reminders"},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc
