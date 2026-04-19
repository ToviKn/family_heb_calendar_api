import logging
from typing import Annotated, cast

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.user import UserCreate, UserResponse
from services import user_service
from storage.database import get_db

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: DbSession) -> UserResponse:
    return cast(UserResponse, user_service.create_user(db, user.email, user.name, user.password))