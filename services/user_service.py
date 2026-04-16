import logging
import re

from sqlalchemy.orm import Session

from exceptions import CalendarAPIException, ConflictError, DatabaseError, ValidationError
from models.models import User
from services.auth_service import hash_password

logger = logging.getLogger(__name__)
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


def create_user(db: Session, email: str, name: str, password: str) -> User:
    logger.info("User creation started", extra={"operation": "create_user", "user_id": None, "entity_id": None})

    normalized_email = email.strip().lower()
    if not EMAIL_REGEX.fullmatch(normalized_email):
        raise ValidationError("Invalid email format", "email")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters", "password")

    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        logger.warning(
            "User creation conflict: email already exists",
            extra={"operation": "create_user", "email": normalized_email},
        )
        raise ConflictError("Email already exists", {"email": normalized_email})

    user = User(email=normalized_email, name=name, password_hash=hash_password(password))

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("User creation completed", extra={"operation": "create_user", "user_id": user.id, "entity_id": user.id})
        return user
    except CalendarAPIException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("User creation failed", exc_info=True, extra={"operation": "create_user"})
        raise DatabaseError(f"Failed to create user: {exc}", "create_user") from exc
