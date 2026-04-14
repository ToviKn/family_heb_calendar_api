import logging
import os
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from exceptions import CalendarAPIException, DatabaseError, ValidationError
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
    return pwd_context.hash(password[:MAX_BCRYPT_LENGTH])


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "iat": datetime.utcnow()}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def _extract_user_id_from_payload(payload: dict[str, object]) -> int:
    if "sub" not in payload:
        raise CalendarAPIException("Invalid token", 401)

    user_id_raw = payload.get("sub")
    if not isinstance(user_id_raw, (str, int)):
        raise CalendarAPIException("Invalid user ID in token", 401)

    try:
        return int(user_id_raw)
    except (TypeError, ValueError) as exc:
        raise CalendarAPIException("Invalid user ID in token", 401) from exc


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = _extract_user_id_from_payload(payload)
    except CalendarAPIException:
        raise
    except JWTError as exc:
        raise CalendarAPIException("Invalid token", 401) from exc

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise CalendarAPIException("User not found", 401)
        return user
    except CalendarAPIException:
        raise
    except Exception as exc:
        logger.error("Failed to resolve authenticated user", exc_info=True)
        raise DatabaseError(f"Failed to resolve authenticated user: {exc}", "get_current_user") from exc
