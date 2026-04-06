import logging
from datetime import date
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from exceptions import CalendarAPIException
from models.event import EventCreate, EventListResponse, EventResponse, EventUpdate
from models.models import User
from services import event_service
from services.auth_service import get_current_user
from storage.database import get_db

router = APIRouter(prefix="/events", tags=["events"])
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _log_route_error(operation: str, exc: Exception, **context: object) -> None:
    logger.error(
        "Event route failed",
        exc_info=True,
        extra={"operation": operation, "error_type": exc.__class__.__name__, **context},
    )


@router.post("/", response_model=EventResponse, status_code=201)
async def create_event(
    request: Request, event: EventCreate, db: DbSession, current_user: CurrentUser
) -> EventResponse:
    """Create a new event."""
    logger.info(
        "Create event request started",
        extra={"operation": "create_event", "user_id": current_user.id},
    )
    try:
        payload = await request.json()
        if isinstance(payload, dict) and "created_by" in payload:
            logger.warning(
                "Create event request attempted to set created_by",
                extra={"operation": "create_event", "user_id": current_user.id},
            )
        created = cast(EventResponse, event_service.create_event(db, event, current_user.id))
        logger.info(
            "Create event request completed",
            extra={
                "operation": "create_event",
                "user_id": current_user.id,
                "event_id": created.id,
            },
        )
        return created
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        _log_route_error("create_event", exc, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/", response_model=list[EventResponse])
def search_by_date(
    db: DbSession,
    current_user: CurrentUser,
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month", ge=1, le=12),
    day: int = Query(..., description="Day", ge=1, le=31),
) -> list[EventResponse]:
    """Search events by Gregorian date."""
    logger.info(
        "Search events request started",
        extra={
            "operation": "search_events_by_date",
            "user_id": current_user.id,
            "year": year,
            "month": month,
            "day": day,
        },
    )
    try:
        family_ids = event_service.get_user_family_ids(current_user, db)
        results = cast(
            list[EventResponse],
            event_service.get_events_for_date(db, year, month, day, family_ids=family_ids),
        )
        logger.info(
            "Search events request completed",
            extra={"operation": "search_events_by_date", "user_id": current_user.id, "result_count": len(results)},
        )
        return results
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        _log_route_error("search_events_by_date", exc, user_id=current_user.id, year=year, month=month, day=day)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/today", response_model=list[EventResponse])
def events_today(db: DbSession, current_user: CurrentUser) -> list[EventResponse]:
    """Get today's events."""
    try:
        today = date.today()
        logger.info(
            "Get today's events request started",
            extra={"operation": "events_today", "user_id": current_user.id, "date": today.isoformat()},
        )
        family_ids = event_service.get_user_family_ids(current_user, db)
        results = cast(
            list[EventResponse],
            event_service.get_events_for_date(
                db, today.year, today.month, today.day, family_ids=family_ids
            ),
        )
        logger.info(
            "Get today's events request completed",
            extra={"operation": "events_today", "user_id": current_user.id, "result_count": len(results)},
        )
        return results
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        _log_route_error("events_today", exc, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/upcoming", response_model=list[EventResponse])
def upcoming_events(
    db: DbSession,
    current_user: CurrentUser,
    days: int = Query(30, description="Number of days ahead", ge=1, le=365),
    family_id: int | None = Query(None, description="Filter by family ID"),
) -> list[EventResponse]:
    """Get upcoming events for the next N days."""
    logger.info(
        "Upcoming events request started",
        extra={"operation": "upcoming_events", "user_id": current_user.id, "days": days, "family_id": family_id},
    )
    try:
        family_ids = event_service.get_user_family_ids(current_user, db)
        if family_id is not None and family_id not in family_ids:
            logger.warning(
                "Unauthorized upcoming events family filter attempt",
                extra={"operation": "upcoming_events", "user_id": current_user.id, "family_id": family_id},
            )
            return []

        results = cast(
            list[EventResponse],
            event_service.get_upcoming_events(
                db, days, family_id, allowed_family_ids=family_ids
            ),
        )
        logger.info(
            "Upcoming events request completed",
            extra={"operation": "upcoming_events", "user_id": current_user.id, "result_count": len(results)},
        )
        return results
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        _log_route_error("upcoming_events", exc, user_id=current_user.id, days=days, family_id=family_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/family/{family_id}", response_model=EventListResponse)
def family_events(
    family_id: int,
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, description="Page number", ge=1),
    per_page: int = Query(20, description="Items per page", ge=1, le=100),
) -> EventListResponse:
    """Get paginated events for a specific family."""
    logger.info(
        "Family events request started",
        extra={
            "operation": "family_events",
            "user_id": current_user.id,
            "family_id": family_id,
            "page": page,
            "per_page": per_page,
        },
    )
    try:
        family_ids = event_service.get_user_family_ids(current_user, db)
        result = event_service.get_events_by_family(
            db, family_id, page, per_page, allowed_family_ids=family_ids
        )
        logger.info(
            "Family events request completed",
            extra={
                "operation": "family_events",
                "user_id": current_user.id,
                "family_id": family_id,
                "result_count": len(result["events"]),
            },
        )
        return EventListResponse(**result)
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        _log_route_error(
            "family_events", exc, user_id=current_user.id, family_id=family_id, page=page, per_page=per_page
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: DbSession, current_user: CurrentUser) -> EventResponse:
    """Get a specific event by ID."""
    logger.info(
        "Get event request started", extra={"operation": "get_event", "event_id": event_id, "user_id": current_user.id}
    )
    try:
        family_ids = event_service.get_user_family_ids(current_user, db)
        event = cast(EventResponse, event_service.get_event_by_id(db, event_id))
        if event.family_id not in family_ids:
            logger.warning(
                "Unauthorized event fetch attempt",
                extra={
                    "operation": "get_event",
                    "event_id": event_id,
                    "family_id": event.family_id,
                    "user_id": current_user.id,
                },
            )
            raise HTTPException(status_code=403, detail="Not authorized to access this event")
        logger.info(
            "Get event request completed",
            extra={
                "operation": "get_event",
                "event_id": event_id,
                "family_id": event.family_id,
                "user_id": current_user.id,
            },
        )
        return event
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        _log_route_error("get_event", exc, event_id=event_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int, request: Request, event: EventUpdate, db: DbSession, current_user: CurrentUser
) -> EventResponse:
    """Update an event (partial update supported)."""
    logger.info(
        "Update event request started",
        extra={"operation": "update_event", "event_id": event_id, "user_id": current_user.id},
    )
    try:
        payload = await request.json()
        if isinstance(payload, dict) and "created_by" in payload:
            logger.warning(
                "Update event request attempted to set created_by",
                extra={"operation": "update_event", "event_id": event_id, "user_id": current_user.id},
            )
        updated = cast(EventResponse, event_service.update_event(db, event_id, event, current_user.id))
        logger.info(
            "Update event request completed",
            extra={
                "operation": "update_event",
                "event_id": event_id,
                "family_id": updated.family_id,
                "user_id": current_user.id,
            },
        )
        return updated
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        _log_route_error("update_event", exc, event_id=event_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/{event_id}")
def delete_event(event_id: int, db: DbSession, current_user: CurrentUser) -> dict[str, str]:
    """Delete an event."""
    logger.info(
        "Delete event request started",
        extra={"operation": "delete_event", "event_id": event_id, "user_id": current_user.id},
    )
    try:
        result = event_service.delete_event(db, event_id, current_user.id)
        logger.info(
            "Delete event request completed",
            extra={"operation": "delete_event", "event_id": event_id, "user_id": current_user.id},
        )
        return result
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        _log_route_error("delete_event", exc, event_id=event_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
