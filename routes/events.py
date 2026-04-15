import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from exceptions import CalendarAPIException
from models.event import EventCreate, EventListResponse, EventResponse, EventUpdate
from models.models import User
from services import event_service
from services.auth_service import get_current_user
from services.family_service import get_user_family_ids
from storage.database import get_db

router = APIRouter(prefix="/events", tags=["events"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _as_http(exc: CalendarAPIException) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "details": exc.details},
    )


@router.post("/", response_model=EventResponse, status_code=201)
async def create_event(request: Request, event: EventCreate, db: DbSession, current_user: CurrentUser) -> EventResponse:
    try:
        payload = await request.json()
        if isinstance(payload, dict) and "created_by" in payload:
            logger.warning("Create event request attempted to set created_by", extra={"operation": "create_event", "user_id": current_user.id})
        return event_service.create_event(db, event, current_user.id)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.get("/", response_model=list[EventResponse])
def search_by_date(
    db: DbSession,
    current_user: CurrentUser,
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month", ge=1, le=12),
    day: int = Query(..., description="Day", ge=1, le=31),
) -> list[EventResponse]:
    try:
        family_ids = get_user_family_ids(db, current_user.id)
        return event_service.get_events_for_date(db, year, month, day, family_ids=family_ids)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.get("/today", response_model=list[EventResponse])
def events_today(db: DbSession, current_user: CurrentUser) -> list[EventResponse]:
    try:
        today = date.today()
        family_ids = get_user_family_ids(db, current_user.id)
        return event_service.get_events_for_date(db, today.year, today.month, today.day, family_ids=family_ids)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.get("/upcoming", response_model=list[EventResponse])
def upcoming_events(
    db: DbSession,
    current_user: CurrentUser,
    days: int = Query(30, description="Number of days ahead", ge=1, le=365),
    family_id: int | None = Query(None, description="Filter by family ID"),
) -> list[EventResponse]:
    try:
        family_ids = get_user_family_ids(db, current_user.id)
        return event_service.get_upcoming_events(db, days, family_id, allowed_family_ids=family_ids)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.get("/family/{family_id}", response_model=EventListResponse)
def family_events(
    family_id: int,
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, description="Page number", ge=1),
    per_page: int = Query(20, description="Items per page", ge=1, le=100),
) -> EventListResponse:
    try:
        family_ids = get_user_family_ids(db, current_user.id)
        result = event_service.get_events_by_family(db, family_id, page, per_page, allowed_family_ids=family_ids)
        return EventListResponse(**result)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: DbSession, current_user: CurrentUser) -> EventResponse:
    try:
        return event_service.get_event_by_id(db, event_id, user_id=current_user.id)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(event_id: int, request: Request, event: EventUpdate, db: DbSession, current_user: CurrentUser) -> EventResponse:
    try:
        payload = await request.json()
        if isinstance(payload, dict) and "created_by" in payload:
            logger.warning("Update event request attempted to set created_by", extra={"operation": "update_event", "event_id": event_id, "user_id": current_user.id})
        return event_service.update_event(db, event_id, event, current_user.id)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc


@router.delete("/{event_id}")
def delete_event(event_id: int, db: DbSession, current_user: CurrentUser) -> dict[str, str]:
    try:
        return event_service.delete_event(db, event_id, current_user.id)
    except CalendarAPIException as exc:
        raise _as_http(exc) from exc
