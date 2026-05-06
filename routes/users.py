import logging
from typing import Annotated, cast

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.models import User
from models.user import ChangePasswordRequest, UserCreate, UserResponse
from services.auth_service import get_current_user
from services import user_service
from storage.database import get_db

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: DbSession) -> UserResponse:
    return cast(UserResponse, user_service.create_user(db, user.email, user.name, user.password))


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    user_service.change_password(db, current_user, payload.current_password, payload.new_password)
    return {"status": "success", "message": "Password updated successfully"}
