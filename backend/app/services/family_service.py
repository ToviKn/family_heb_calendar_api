import logging
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.exceptions import (
    CalendarAPIException,
    ConflictError,
    DatabaseError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.models.models import Family, FamilyJoinRequest, FamilyMembership, Notification, User
from app.services.notification_dispatcher import dispatch_notification
from app.storage.enums import NotificationType

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


def _get_family_or_raise(db: Session, family_id: int) -> Family:
    family = db.query(Family).filter(Family.id == family_id).first()
    if family is None:
        raise NotFoundError("Family", family_id)
    return family


def _get_user_or_raise(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise NotFoundError("User", user_id)
    return user


def _get_existing_membership(db: Session, family_id: int, user_id: int) -> FamilyMembership | None:
    return (
        db.query(FamilyMembership)
        .filter(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == family_id,
        )
        .first()
    )


def _ensure_not_member(db: Session, family_id: int, user_id: int) -> None:
    if _get_existing_membership(db, family_id, user_id) is not None:
        raise ConflictError(
            "User is already a member of this family",
            {"user_id": user_id, "family_id": family_id},
        )


def _get_pending_join_request(db: Session, family_id: int, user_id: int) -> FamilyJoinRequest | None:
    return (
        db.query(FamilyJoinRequest)
        .filter(
            FamilyJoinRequest.user_id == user_id,
            FamilyJoinRequest.family_id == family_id,
            FamilyJoinRequest.status == "pending",
        )
        .first()
    )


def _get_pending_join_request_by_id(db: Session, family_id: int, request_id: int) -> FamilyJoinRequest:
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
    return join_request


def _create_membership(db: Session, family_id: int, user_id: int) -> FamilyMembership:
    membership = FamilyMembership(user_id=user_id, family_id=family_id)
    db.add(membership)
    return membership


def _add_notification(
    db: Session,
    user_id: int,
    message: str,
    notification_type: NotificationType,
    metadata_json: dict | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        event_id=None,
        message=message,
        metadata_json=metadata_json,
        type=notification_type.value,
        is_read=False,
        created_at=datetime.utcnow(),
        sent=True,
        send_at=datetime.utcnow(),
    )
    db.add(notification)
    return notification


def _notify_admins_of_join_request(db: Session, family: Family, request_user: User) -> list[Notification]:
    notifications: list[Notification] = []
    admin_memberships = (
        db.query(FamilyMembership)
        .filter(FamilyMembership.family_id == family.id, FamilyMembership.role == "admin")
        .all()
    )
    for admin_membership in admin_memberships:
        notifications.append(
            _add_notification(
                db=db,
                user_id=admin_membership.user_id,
                message=f"{request_user.name} requested to join family {family.name}",
                notification_type=NotificationType.JOIN_REQUEST,
                metadata_json={
                    "actor": {"id": request_user.id, "name": request_user.name},
                    "target": {"id": request_user.id, "name": request_user.name},
                    "requesting_user_id": request_user.id,
                    "requesting_user_name": request_user.name,
                    "family_id": family.id,
                    "family_name": family.name,
                },
            )
        )

    return notifications


def _notify_user_directly_added(db: Session, family: Family, added_user: User, actor_user: User) -> Notification:
    return _add_notification(
        db=db,
        user_id=added_user.id,
        message=f"{actor_user.name} invited {added_user.name} to family {family.name}",
        notification_type=NotificationType.INVITE,
        metadata_json={
            "actor": {"id": actor_user.id, "name": actor_user.name},
            "target": {"id": added_user.id, "name": added_user.name},
            "family_id": family.id,
            "family_name": family.name,
        },
    )


def _notify_user_join_request_approved(db: Session, family: Family, request_user: User, actor_user: User) -> Notification:
    return _add_notification(
        db=db,
        user_id=request_user.id,
        message=f"{actor_user.name} approved your request to join family {family.name}",
        notification_type=NotificationType.JOIN_REQUEST,
        metadata_json={
            "actor": {"id": actor_user.id, "name": actor_user.name},
            "target": {"id": request_user.id, "name": request_user.name},
            "family_id": family.id,
            "family_name": family.name,
            "status": "approved",
        },
    )


def _notify_user_join_request_rejected(db: Session, family: Family, request_user: User, actor_user: User) -> Notification:
    return _add_notification(
        db=db,
        user_id=request_user.id,
        message=f"{actor_user.name} rejected your request to join family {family.name}",
        notification_type=NotificationType.JOIN_REQUEST,
        metadata_json={
            "actor": {"id": actor_user.id, "name": actor_user.name},
            "target": {"id": request_user.id, "name": request_user.name},
            "family_id": family.id,
            "family_name": family.name,
            "status": "rejected",
        },
    )


def add_member(db: Session, family_id: int, user_id: int, actor_user_id: int) -> FamilyMembership:
    try:
        family = _get_family_or_raise(db, family_id)
        ensure_admin_in_family(db, actor_user_id, family_id)
        target_user = _get_user_or_raise(db, user_id)
        actor_user = _get_user_or_raise(db, actor_user_id)
        _ensure_not_member(db, family_id, user_id)

        membership = _create_membership(db, family_id, user_id)
        pending_request = _get_pending_join_request(db, family_id, user_id)
        if pending_request is not None:
            db.delete(pending_request)
        notification = _notify_user_directly_added(db, family, target_user, actor_user)
        db.commit()
        db.refresh(notification)
        dispatch_notification(db, notification)
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


def create_join_request(db: Session, family_id: int, actor_user_id: int) -> dict[str, str]:
    try:
        family = _get_family_or_raise(db, family_id)
        request_user = _get_user_or_raise(db, actor_user_id)
        _ensure_not_member(db, family_id, actor_user_id)

        existing_request = _get_pending_join_request(db, family_id, actor_user_id)
        if existing_request is not None:
            logger.warning(
                "Duplicate pending join request",
                extra={"operation": "create_join_request", "user_id": actor_user_id, "family_id": family_id},
            )
            return {"status": "pending", "message": "Join request already pending"}

        join_request = FamilyJoinRequest(
            user_id=actor_user_id,
            family_id=family_id,
            requested_by=actor_user_id,
            status="pending",
        )
        db.add(join_request)
        notifications = _notify_admins_of_join_request(db, family, request_user)
        db.commit()
        for notification in notifications:
            db.refresh(notification)
            dispatch_notification(db, notification)

        logger.info(
            "Join request created",
            extra={"operation": "create_join_request", "user_id": actor_user_id, "family_id": family_id},
        )
        return {"status": "pending", "message": "Join request sent to family admins"}
    except (CalendarAPIException, NotFoundError, ValidationError):
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "Join request already pending or invalid user/family",
            {"user_id": actor_user_id, "family_id": family_id},
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(
            "Failed to create join request",
            exc_info=True,
            extra={"operation": "create_join_request", "user_id": actor_user_id, "family_id": family_id},
        )
        raise DatabaseError(f"Failed to create join request: {exc}", "create_join_request") from exc


def list_pending_join_requests(db: Session, family_id: int, actor_user_id: int) -> list[dict[str, object]]:
    family = _get_family_or_raise(db, family_id)
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
            "family_name": family.name,
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
        family = _get_family_or_raise(db, family_id)
        ensure_admin_in_family(db, actor_user_id, family_id)
        actor_user = _get_user_or_raise(db, actor_user_id)
        join_request = _get_pending_join_request_by_id(db, family_id, request_id)
        request_user = _get_user_or_raise(db, join_request.user_id)

        existing_membership = _get_existing_membership(db, family_id, join_request.user_id)
        if existing_membership is not None:
            db.delete(join_request)
            notification = _notify_user_join_request_approved(db, family, request_user, actor_user)
            db.commit()
            db.refresh(notification)
            dispatch_notification(db, notification)
            db.refresh(existing_membership)
            return existing_membership

        membership = _create_membership(db, family_id, join_request.user_id)
        db.delete(join_request)
        notification = _notify_user_join_request_approved(db, family, request_user, actor_user)
        db.commit()
        db.refresh(notification)
        dispatch_notification(db, notification)
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
        family = _get_family_or_raise(db, family_id)
        ensure_admin_in_family(db, actor_user_id, family_id)
        actor_user = _get_user_or_raise(db, actor_user_id)
        join_request = _get_pending_join_request_by_id(db, family_id, request_id)
        request_user = _get_user_or_raise(db, join_request.user_id)

        db.delete(join_request)
        notification = _notify_user_join_request_rejected(db, family, request_user, actor_user)
        db.commit()
        db.refresh(notification)
        dispatch_notification(db, notification)

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
