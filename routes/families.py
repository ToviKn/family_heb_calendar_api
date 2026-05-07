import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.family import (
    FamilyJoinRequestListResponse,
    FamilyJoinRequestResponse,
    FamilyMembershipResponse,
    FamilyResponse,
)
from models.models import User
from services import notification_service
from services.auth_service import get_current_user
from services.family_service import add_member as add_member_service
from services.family_service import approve_join_request as approve_join_request_service
from services.family_service import create_family as create_family_service
from services.family_service import list_pending_join_requests as list_pending_join_requests_service
from services.family_service import reject_join_request as reject_join_request_service
from storage.database import get_db

router = APIRouter(prefix="/families", tags=["families"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.post("/", response_model=FamilyResponse)
def create_family(name: str, db: DbSession, current_user: CurrentUser) -> FamilyResponse:
    return FamilyResponse.model_validate(create_family_service(db, name, current_user.id))


@router.post("/{family_id}/members", response_model=FamilyMembershipResponse | FamilyJoinRequestResponse)
def add_member(family_id: int, user_id: int, db: DbSession, current_user: CurrentUser) -> FamilyMembershipResponse | FamilyJoinRequestResponse:
    result = add_member_service(db, family_id, user_id, current_user.id)
    if isinstance(result, dict):
        return FamilyJoinRequestResponse.model_validate(result)

    notification_service.notify_family_invitation(
        db,
        invited_user_id=user_id,
        family_id=family_id,
        invited_by_user_id=current_user.id,
    )
    logger.info(
        "Invite notification sent",
        extra={"operation": "add_member", "user_id": current_user.id, "family_id": family_id, "added_user_id": user_id},
    )
    logger.info(
        "Membership changed: member added",
        extra={"operation": "add_member", "family_id": family_id, "user_id": current_user.id, "entity_id": result.id},
    )
    return FamilyMembershipResponse.model_validate(result)


@router.post("/{family_id}/join-requests", response_model=FamilyJoinRequestResponse)
def request_to_join_family(family_id: int, db: DbSession, current_user: CurrentUser) -> FamilyJoinRequestResponse:
    result = add_member_service(db, family_id, current_user.id, current_user.id)
    if not isinstance(result, dict):
        return FamilyJoinRequestResponse(status="joined", message="Already joined family")
    return FamilyJoinRequestResponse.model_validate(result)


@router.get("/{family_id}/join-requests", response_model=FamilyJoinRequestListResponse)
def list_join_requests(family_id: int, db: DbSession, current_user: CurrentUser) -> FamilyJoinRequestListResponse:
    requests = list_pending_join_requests_service(db, family_id, current_user.id)
    return FamilyJoinRequestListResponse.model_validate({"requests": requests, "total": len(requests)})


@router.post("/{family_id}/join-requests/{request_id}/approve", response_model=FamilyMembershipResponse)
def approve_join_request(
    family_id: int,
    request_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> FamilyMembershipResponse:
    membership = approve_join_request_service(db, family_id, request_id, current_user.id)
    return FamilyMembershipResponse.model_validate(membership)


@router.delete("/{family_id}/join-requests/{request_id}", response_model=FamilyJoinRequestResponse)
def reject_join_request(
    family_id: int,
    request_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> FamilyJoinRequestResponse:
    result = reject_join_request_service(db, family_id, request_id, current_user.id)
    return FamilyJoinRequestResponse.model_validate(result)
