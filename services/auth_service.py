import logging
import os
from datetime import datetime, timedelta
from typing import Annotated, cast

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models.models import User
from storage.database import get_db

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required")
ALGORITHM = "HS256"
MAX_BCRYPT_LENGTH = 72
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
DbSession = Annotated[Session, Depends(get_db)]


def hash_password(password: str) -> str:
    password = password[:MAX_BCRYPT_LENGTH]
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(
        "Access token created",
        extra={"operation": "create_access_token", "user_id": user_id, "token_expiration": expire.isoformat()},
    )
    return token


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    logger.info("Authentication started", extra={"operation": "authenticate_user"})
    user = cast(User | None, db.query(User).filter(User.email == email).first())

    if not user:
        logger.warning("Authentication failed: unknown email", extra={"operation": "authenticate_user"})
        return None

    if not verify_password(password, user.password_hash):
        logger.warning(
            "Authentication failed: invalid credentials",
            extra={"operation": "authenticate_user", "user_id": user.id},
        )
        return None

    logger.info(
        "Authentication completed",
        extra={"operation": "authenticate_user", "user_id": user.id},
    )
    return user


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_sub": False},
        )
        user_id_raw = payload.get("sub")

        if user_id_raw is None:
            logger.warning("Token rejected: missing subject claim")
            raise HTTPException(status_code=401, detail="Invalid token")

        if not isinstance(user_id_raw, (str, int)):
            logger.warning(
                "Token rejected: invalid subject type",
                extra={"subject_type": type(user_id_raw).__name__},
            )
            raise HTTPException(status_code=401, detail="Invalid user ID in token")

        try:
            user_id = int(user_id_raw)
        except (TypeError, ValueError) as exc:
            logger.warning(
                "Token rejected: invalid subject value", extra={"subject": user_id_raw}
            )
            raise HTTPException(
                status_code=401, detail="Invalid user ID in token"
            ) from exc

    except JWTError as exc:
        logger.warning("Token rejected: JWT decode failure")
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    user = cast(User | None, db.query(User).filter(User.id == user_id).first())

    if user is None:
        logger.warning("Token rejected: user not found", extra={"user_id": user_id})
        raise HTTPException(status_code=401, detail="User not found")

    logger.debug("Authenticated request user resolved", extra={"user_id": user_id})
    return user
