import logging
import re

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from exceptions import CalendarAPIException, ConflictError, DatabaseError, ValidationError
from models.models import User
from services.auth_service import hash_password

logger = logging.getLogger(__name__)
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128
MAX_BCRYPT_LENGTH = 72

PASSWORD_REGEX = {
    "lower": re.compile(r"[a-z]"),
    "upper": re.compile(r"[A-Z]"),
    "digit": re.compile(r"\d"),
    "special": re.compile(r"[!@#$%^&*(),.?\":{}|<>_\-\\[\]/+=~`]")
}


def validate_password(password: str, email: str | None = None) -> None:
    if not password or password.strip() == "":
        raise ValidationError("Password cannot be empty", "password")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters",
            "password",
        )

    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValidationError("Password too long", "password")

    if len(password.encode("utf-8")) > MAX_BCRYPT_LENGTH:
        raise ValidationError(
            "Password too long (max 72 bytes for hashing)",
            "password"
        )

    if not PASSWORD_REGEX["lower"].search(password):
        raise ValidationError("Password must include a lowercase letter", "password")

    if not PASSWORD_REGEX["upper"].search(password):
        raise ValidationError("Password must include an uppercase letter", "password")

    if not PASSWORD_REGEX["digit"].search(password):
        raise ValidationError("Password must include a number", "password")

    if not PASSWORD_REGEX["special"].search(password):
        raise ValidationError("Password must include a special character", "password")

    if email and email.lower() in password.lower():
        raise ValidationError("Password cannot contain your email", "password")

def create_user(db: Session, email: str, name: str, password: str) -> User:
    logger.info("User creation started", extra={"operation": "create_user", "user_id": None, "entity_id": None})

    normalized_email = email.strip().lower()
    if not EMAIL_REGEX.fullmatch(normalized_email):
        raise ValidationError("Invalid email format", "email")

    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        logger.warning(
            "User creation conflict: email already exists",
            extra={"operation": "create_user", "email": normalized_email},
        )
        raise ConflictError("Email already exists", {"email": normalized_email})

    validate_password(password, normalized_email)
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
    except IntegrityError:
        db.rollback()
        raise ConflictError("Email already exists", {"email": normalized_email})
    except Exception as exc:
        db.rollback()
        logger.error("User creation failed", exc_info=True, extra={"operation": "create_user"})
        raise DatabaseError(f"Failed to create user: {exc}", "create_user") from exc
