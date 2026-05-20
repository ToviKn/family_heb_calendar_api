import logging
import re

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.exceptions import CalendarAPIException, ConflictError, DatabaseError, ValidationError
from app.models.models import User
from app.services.auth_service import hash_password, verify_password

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


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if user is None or not user.password_hash:
        logger.error(
            "Cannot change password: missing user or password hash",
            extra={"operation": "change_password", "user_id": getattr(user, "id", None)},
        )
        raise CalendarAPIException("Unable to change password for this user", 400)

    if not verify_password(current_password, user.password_hash):
        logger.warning(
            "Wrong current password attempt",
            extra={"operation": "change_password", "user_id": user.id},
        )
        raise CalendarAPIException("Current password is incorrect", 400, {"field": "current_password"})
    if verify_password(new_password, user.password_hash):
        logger.warning(
            "Password reuse attempt",
            extra={"operation": "change_password", "user_id": user.id},
        )
        raise CalendarAPIException("New password must be different from current password", 400, {"field": "new_password"})
    try:
        validate_password(new_password, user.email)
    except ValidationError as exc:
        logger.warning(
            "Weak new password attempt",
            extra={"operation": "change_password", "user_id": user.id},
        )
        details = {**exc.details, "field": "new_password"}
        raise CalendarAPIException(exc.message, 400, details) from exc
    user.password_hash = hash_password(new_password)

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(
            "Password changed successfully",
            extra={"operation": "change_password", "user_id": user.id},
        )
        logger.warning(
            "Password changed successfully; existing access tokens remain valid until expiration",
            extra={"operation": "change_password", "user_id": user.id},
        )
    except CalendarAPIException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error(
            "Password change failed",
            exc_info=True,
            extra={"operation": "change_password", "user_id": user.id},
        )
        raise DatabaseError(f"Failed to change password: {exc}", "change_password") from exc
