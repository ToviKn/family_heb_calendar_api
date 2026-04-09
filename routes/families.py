import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.models import Family, FamilyMembership, User
from services.auth_service import get_current_user
from services import notification_service
from storage.database import get_db

router = APIRouter(prefix="/families", tags=["families"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/", response_model=None)
def create_family(
    name: str,
    db: DbSession,
    current_user: CurrentUser,
) -> Any:
    try:
        family = Family(name=name)

        db.add(family)
        db.commit()
        db.refresh(family)
        logger.info(
            "Family created",
            extra={
                "family_id": family.id,
                "family_name": name,
                "created_by": current_user.id,
            },
        )

        membership = FamilyMembership(
            user_id=current_user.id, family_id=family.id, role="admin"
        )

        db.add(membership)
        db.commit()
        logger.info(
            "Membership created",
            extra={"family_id": family.id, "user_id": current_user.id, "role": "admin"},
        )

        return family
    except Exception:
        db.rollback()
        logger.error(
            "Failed to create family",
            exc_info=True,
            extra={"created_by": current_user.id},
        )
        raise


@router.post("/{family_id}/members", response_model=None)
def add_member(
    family_id: int,
    user_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Any:
    try:
        actor_membership = (
            db.query(FamilyMembership)
            .filter(
                FamilyMembership.user_id == current_user.id,
                FamilyMembership.family_id == family_id,
            )
            .first()
        )
        if not actor_membership or actor_membership.role != "admin":
            logger.warning(
                "Unauthorized family membership add attempt",
                extra={"user_id": current_user.id, "family_id": family_id},
            )
            raise HTTPException(status_code=403, detail="Not authorized to add family members")

        existing_membership = (
            db.query(FamilyMembership)
            .filter(
                FamilyMembership.user_id == user_id,
                FamilyMembership.family_id == family_id,
            )
            .first()
        )
        if existing_membership:
            logger.warning(
                "Membership change rejected: user already in family",
                extra={
                    "family_id": family_id,
                    "user_id": current_user.id,
                    "added_user_id": user_id,
                },
            )
            raise HTTPException(status_code=400, detail="User is already a member of this family")

        membership = FamilyMembership(user_id=user_id, family_id=family_id)

        db.add(membership)
        db.commit()
        logger.info(
            "Membership changed: member added",
            extra={
                "family_id": family_id,
                "user_id": current_user.id,
                "added_user_id": user_id,
            },
        )
        notification_service.notify_family_invitation(
            db,
            invited_user_id=user_id,
            family_id=family_id,
            invited_by_user_id=current_user.id,
        )

        return membership
    except IntegrityError as exc:
        db.rollback()
        logger.warning(
            "Membership change rejected: duplicate or invalid relation",
            extra={
                "family_id": family_id,
                "user_id": current_user.id,
                "added_user_id": user_id,
            },
        )
        raise HTTPException(
            status_code=400, detail="Membership already exists or invalid user/family"
        ) from exc
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.error(
            "Failed to add family member",
            exc_info=True,
            extra={
                "family_id": family_id,
                "user_id": user_id,
                "added_by": current_user.id,
            },
        )
        raise
