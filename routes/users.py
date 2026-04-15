import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from exceptions import CalendarAPIException
from models.user import UserCreate, UserResponse
from services import user_service
from storage.database import get_db

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]


def _as_http(exc: CalendarAPIException) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "details": exc.details},
    )


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: DbSession) -> UserResponse:
    try:
        return user_service.create_user(db, user.email, user.name, user.password)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc
