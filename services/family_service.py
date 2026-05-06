import logging
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from exceptions import (
    CalendarAPIException,
    ConflictError,
    DatabaseError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from models.models import Family, FamilyJoinRequest, FamilyMembership, Notification, User

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


def add_member(db: Session, family_id: int, user_id: int, actor_user_id: int) -> FamilyMembership | dict[str, str]:
    try:
        actor_membership = (
            db.query(FamilyMembership)
            .filter(
                FamilyMembership.user_id == actor_user_id,
                FamilyMembership.family_id == family_id,
            )
            .first()
        )
        is_admin = actor_membership is not None and actor_membership.role == "admin"

        family = db.query(Family).filter(Family.id == family_id).first()
        if family is None:
            raise NotFoundError("Family", family_id)

        target_user = db.query(User).filter(User.id == user_id).first()
        if target_user is None:
            raise NotFoundError("User", user_id)
        actor_user = db.query(User).filter(User.id == actor_user_id).first()
        if actor_user is None:
            raise NotFoundError("User", actor_user_id)

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

        if not is_admin:
            existing_request = (
                db.query(FamilyJoinRequest)
                .filter(
                    FamilyJoinRequest.user_id == user_id,
                    FamilyJoinRequest.family_id == family_id,
                    FamilyJoinRequest.status == "pending",
                )
                .first()
            )
            if existing_request is not None:
                logger.warning(
                    "Duplicate pending join request",
                    extra={"operation": "add_family_member", "user_id": actor_user_id, "family_id": family_id, "added_user_id": user_id},
                )
                return {"status": "pending", "message": "Join request already pending"}

            join_request = FamilyJoinRequest(
                user_id=user_id,
                family_id=family_id,
                requested_by=actor_user_id,
                status="pending",
            )
            db.add(join_request)

            admin_memberships = (
                db.query(FamilyMembership)
                .filter(FamilyMembership.family_id == family_id, FamilyMembership.role == "admin")
                .all()
            )
            for admin_membership in admin_memberships:
                notification = Notification(
                    user_id=admin_membership.user_id,
                    event_id=None,
                    message=(
                        f"{actor_user.name} requested to add {target_user.name} to family {family.name}"
                    ),
                    metadata_json={
                        "actor": {"id": actor_user.id, "name": actor_user.name},
                        "target": {"id": target_user.id, "name": target_user.name},
                        "family_id": family_id,
                        "family_name": family.name,
                    },
                    type="join_request",
                    is_read=False,
                    created_at=datetime.utcnow(),
                )
                db.add(notification)

            db.commit()
            logger.info(
                "Join request created",
                extra={"operation": "add_family_member", "actor_user_id": actor_user_id, "user_id": user_id, "family_id": family_id},
            )
            return {"status": "pending", "message": "Join request sent to family admins"}

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


def _get_family_or_raise(db: Session, family_id: int) -> Family:
    family = db.query(Family).filter(Family.id == family_id).first()
    if family is None:
        raise NotFoundError("Family", family_id)
    return family


def list_pending_join_requests(db: Session, family_id: int, actor_user_id: int) -> list[dict[str, object]]:
    _get_family_or_raise(db, family_id)
    ensure_admin_in_family(db, actor_user_id, family_id)

    request_user = aliased(User)
    requester_user = aliased(User)
    requests = (
        db.query(FamilyJoinRequest, request_user, requester_user)
        .join(request_user, FamilyJoinRequest.user_id == request_user.id)
        .join(requester_user, FamilyJoinRequest.requested_by == requester_user.id)
        .filter(
            FamilyJoinRequest.family_id == family_id,
            FamilyJoinRequest.status == "pending",
        )
        .order_by(FamilyJoinRequest.created_at.asc())
        .all()
    )

    return [
        {
            "id": join_request.id,
            "user_id": join_request.user_id,
            "family_id": join_request.family_id,
            "requested_by": join_request.requested_by,
            "status": join_request.status,
            "created_at": join_request.created_at,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            },
            "requested_by_user": {
                "id": requested_by_user.id,
                "name": requested_by_user.name,
                "email": requested_by_user.email,
            },
        }
        for join_request, user, requested_by_user in requests
    ]


def approve_join_request(db: Session, family_id: int, request_id: int, actor_user_id: int) -> FamilyMembership:
    try:
        _get_family_or_raise(db, family_id)
        ensure_admin_in_family(db, actor_user_id, family_id)

        join_request = (
            db.query(FamilyJoinRequest)
            .filter(
                FamilyJoinRequest.id == request_id,
                FamilyJoinRequest.family_id == family_id,
                FamilyJoinRequest.status == "pending",
            )
            .first()
        )
        if join_request is None:
            raise NotFoundError("Family join request", request_id)

        existing_membership = (
            db.query(FamilyMembership)
            .filter(
                FamilyMembership.user_id == join_request.user_id,
                FamilyMembership.family_id == family_id,
            )
            .first()
        )
        if existing_membership is not None:
            db.delete(join_request)
            db.commit()
            db.refresh(existing_membership)
            return existing_membership

        membership = FamilyMembership(user_id=join_request.user_id, family_id=family_id)
        db.add(membership)
        db.delete(join_request)
        db.commit()
        db.refresh(membership)

        logger.info(
            "Join request approved",
            extra={
                "operation": "approve_join_request",
                "user_id": actor_user_id,
                "family_id": family_id,
                "entity_id": request_id,
                "added_user_id": membership.user_id,
            },
        )
        return membership
    except CalendarAPIException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "Membership already exists or invalid join request",
            {"family_id": family_id, "request_id": request_id},
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(
            "Failed to approve join request",
            exc_info=True,
            extra={"operation": "approve_join_request", "user_id": actor_user_id, "family_id": family_id},
        )
        raise DatabaseError(f"Failed to approve join request: {exc}", "approve_join_request") from exc


def reject_join_request(db: Session, family_id: int, request_id: int, actor_user_id: int) -> dict[str, str]:
    try:
        _get_family_or_raise(db, family_id)
        ensure_admin_in_family(db, actor_user_id, family_id)

        join_request = (
            db.query(FamilyJoinRequest)
            .filter(
                FamilyJoinRequest.id == request_id,
                FamilyJoinRequest.family_id == family_id,
                FamilyJoinRequest.status == "pending",
            )
            .first()
        )
        if join_request is None:
            raise NotFoundError("Family join request", request_id)

        db.delete(join_request)
        db.commit()

        logger.info(
            "Join request rejected",
            extra={
                "operation": "reject_join_request",
                "user_id": actor_user_id,
                "family_id": family_id,
                "entity_id": request_id,
            },
        )
        return {"status": "rejected", "message": "Join request rejected"}
    except CalendarAPIException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error(
            "Failed to reject join request",
            exc_info=True,
            extra={"operation": "reject_join_request", "user_id": actor_user_id, "family_id": family_id},
        )
        raise DatabaseError(f"Failed to reject join request: {exc}", "reject_join_request") from exc
