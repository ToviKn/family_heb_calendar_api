import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from exceptions import UnauthorizedError
from services.auth_service import authenticate_user, create_access_token
from storage.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]

@router.post("/login", summary="Login with email (use username field as email)")
def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> dict[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "Login request started",
        extra={"operation": "login", "client_ip": client_ip},
    )

    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        logger.warning(
            "Authentication failed at login endpoint",
            extra={"operation": "login", "client_ip": client_ip},
        )
        raise UnauthorizedError("Invalid credentials")

    token = create_access_token(user.id)
    logger.info(
        "Login request completed",
        extra={"operation": "login", "user_id": user.id, "client_ip": client_ip},
    )

    return {"access_token": token, "token_type": "bearer"}
