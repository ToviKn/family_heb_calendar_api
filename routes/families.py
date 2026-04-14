import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from exceptions import CalendarAPIException
from models.models import User
from services import notification_service
from services.auth_service import get_current_user
from services.family_service import add_member as add_member_service
from services.family_service import create_family as create_family_service
from storage.database import get_db

router = APIRouter(prefix="/families", tags=["families"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _as_http(exc: CalendarAPIException) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/", response_model=None)
def create_family(name: str, db: DbSession, current_user: CurrentUser) -> Any:
    try:
        return create_family_service(db, name, current_user.id)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.post("/{family_id}/members", response_model=None)
def add_member(family_id: int, user_id: int, db: DbSession, current_user: CurrentUser) -> Any:
    try:
        membership = add_member_service(db, family_id, user_id, current_user.id)
        notification_service.notify_family_invitation(
            db,
            invited_user_id=user_id,
            family_id=family_id,
            invited_by_user_id=current_user.id,
        )
        logger.info(
            "Membership changed: member added",
            extra={"operation": "add_member", "family_id": family_id, "user_id": current_user.id, "entity_id": membership.id},
        )
        return membership
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc
