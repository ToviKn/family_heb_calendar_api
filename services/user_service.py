import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.models import User
from services.auth_service import hash_password

logger = logging.getLogger(__name__)


def create_user(db: Session, email: str, name: str, password: str) -> User:
    logger.info("User creation started", extra={"operation": "create_user"})
    existing = db.query(User).filter(User.email == email).first()

    if existing:
        logger.warning(
            "User creation failed: email already exists", extra={"operation": "create_user"}
        )
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(email=email, name=name, password_hash=hash_password(password))

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        logger.error("User creation failed", exc_info=True, extra={"operation": "create_user"})
        raise

    logger.info(
        "User creation completed",
        extra={"operation": "create_user", "user_id": user.id},
    )
    return user
