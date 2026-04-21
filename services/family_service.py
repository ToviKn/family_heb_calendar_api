import logging
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from exceptions import (
    CalendarAPIException,
    ConflictError,
    DatabaseError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from models.models import Family, FamilyMembership, User

logger = logging.getLogger(__name__)


def get_user_family_ids(db: Session, user_id: int) -> list[int]:
    memberships = (
        db.query(FamilyMembership.family_id)
        .filter(FamilyMembership.user_id == user_id)
        .all()
    )
    family_ids = [family_id for (family_id,) in memberships]
    logger.debug(
        "Resolved user family memberships",
        extra={"operation": "get_user_family_ids", "user_id": user_id, "family_count": len(family_ids)},
    )
    return family_ids


def ensure_user_in_family(db: Session, user_id: int, family_id: int) -> FamilyMembership:
    membership: FamilyMembership | None = (
        db.query(FamilyMembership)
        .filter(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == family_id,
        )
        .first()
    )
    if membership is None:
        logger.warning(
            "User attempted family access without membership",
            extra={"operation": "ensure_user_in_family", "user_id": user_id, "family_id": family_id},
        )
        raise PermissionDeniedError("User not in family", {"user_id": user_id, "family_id": family_id})
    return membership


def ensure_admin_in_family(db: Session, user_id: int, family_id: int) -> FamilyMembership:
    membership = ensure_user_in_family(db, user_id, family_id)
    if membership.role != "admin":
        logger.warning(
            "Non-admin attempted to manage family members",
            extra={"operation": "ensure_admin_in_family", "user_id": user_id, "family_id": family_id},
        )
        raise PermissionDeniedError(
            "Not authorized to add family members",
            {"user_id": user_id, "family_id": family_id},
        )
    return membership


def create_family(db: Session, name: str, actor_user_id: int) -> Family:
    try:
        family = Family(name=name, created_at=datetime.now(timezone.utc))
        db.add(family)
        db.flush()

        admin_membership = FamilyMembership(
            user_id=actor_user_id,
            family_id=family.id,
            role="admin",
        )
        db.add(admin_membership)
        db.commit()
        db.refresh(family)

        logger.info(
            "Family created",
            extra={"operation": "create_family", "user_id": actor_user_id, "family_id": family.id},
        )
        return family
    except Exception as exc:
        db.rollback()
        logger.error(
            "Failed to create family",
            exc_info=True,
            extra={"operation": "create_family", "user_id": actor_user_id},
        )
        raise DatabaseError(f"Failed to create family: {exc}", "create_family") from exc


def add_member(db: Session, family_id: int, user_id: int, actor_user_id: int) -> FamilyMembership:
    try:
        ensure_admin_in_family(db, actor_user_id, family_id)

        family = db.query(Family).filter(Family.id == family_id).first()
        if family is None:
            raise NotFoundError("Family", family_id)

        target_user = db.query(User).filter(User.id == user_id).first()
        if target_user is None:
            raise NotFoundError("User", user_id)

        existing_membership = (
            db.query(FamilyMembership)
            .filter(
                FamilyMembership.user_id == user_id,
                FamilyMembership.family_id == family_id,
            )
            .first()
        )
        if existing_membership is not None:
            raise ConflictError(
                "User is already a member of this family",
                {"user_id": user_id, "family_id": family_id},
            )

        membership = FamilyMembership(user_id=user_id, family_id=family_id)
        db.add(membership)
        db.commit()
        db.refresh(membership)

        logger.info(
            "Family member added",
            extra={
                "operation": "add_family_member",
                "user_id": actor_user_id,
                "family_id": family_id,
                "entity_id": membership.id,
                "added_user_id": user_id,
            },
        )
        return membership
    except (CalendarAPIException, NotFoundError, ValidationError):
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        logger.warning(
            "Failed to add member due to integrity conflict",
            extra={"operation": "add_family_member", "user_id": actor_user_id, "family_id": family_id, "added_user_id": user_id},
        )
        raise ConflictError(
            "Membership already exists or invalid user/family",
            {"user_id": user_id, "family_id": family_id},
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(
            "Failed to add family member",
            exc_info=True,
            extra={"operation": "add_family_member", "user_id": actor_user_id, "family_id": family_id},
        )
        raise DatabaseError(f"Failed to add family member: {exc}", "add_member") from exc
