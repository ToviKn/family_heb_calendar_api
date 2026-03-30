import logging
from datetime import date
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query
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
def create_event(
    event: EventCreate, db: DbSession, current_user: CurrentUser
) -> EventResponse:
    """Create a new event."""
    logger.info(
        "Create event request started",
        extra={"operation": "create_event", "user_id": current_user.id},
    )
    try:
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
    except Exception as exc:
        _log_route_error("create_event", exc, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/", response_model=list[EventResponse])
def search_by_date(
    db: DbSession,
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month", ge=1, le=12),
    day: int = Query(..., description="Day", ge=1, le=31),
) -> list[EventResponse]:
    """Search events by Gregorian date."""
    logger.info(
        "Search events request started",
        extra={"operation": "search_events_by_date", "year": year, "month": month, "day": day},
    )
    try:
        results = cast(list[EventResponse], event_service.get_events_for_date(db, year, month, day))
        logger.info(
            "Search events request completed",
            extra={"operation": "search_events_by_date", "result_count": len(results)},
        )
        return results
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        _log_route_error("search_events_by_date", exc, year=year, month=month, day=day)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/today", response_model=list[EventResponse])
def events_today(db: DbSession) -> list[EventResponse]:
    """Get today's events."""
    try:
        today = date.today()
        logger.info(
            "Get today's events request started",
            extra={"operation": "events_today", "date": today.isoformat()},
        )
        results = cast(
            list[EventResponse],
            event_service.get_events_for_date(db, today.year, today.month, today.day),
        )
        logger.info(
            "Get today's events request completed",
            extra={"operation": "events_today", "result_count": len(results)},
        )
        return results
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        _log_route_error("events_today", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/upcoming", response_model=list[EventResponse])
def upcoming_events(
    db: DbSession,
    days: int = Query(30, description="Number of days ahead", ge=1, le=365),
    family_id: int | None = Query(None, description="Filter by family ID"),
) -> list[EventResponse]:
    """Get upcoming events for the next N days."""
    logger.info(
        "Upcoming events request started",
        extra={"operation": "upcoming_events", "days": days, "family_id": family_id},
    )
    try:
        results = cast(list[EventResponse], event_service.get_upcoming_events(db, days, family_id))
        logger.info(
            "Upcoming events request completed",
            extra={"operation": "upcoming_events", "result_count": len(results)},
        )
        return results
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        _log_route_error("upcoming_events", exc, days=days, family_id=family_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/family/{family_id}", response_model=EventListResponse)
def family_events(
    family_id: int,
    db: DbSession,
    page: int = Query(1, description="Page number", ge=1),
    per_page: int = Query(20, description="Items per page", ge=1, le=100),
) -> EventListResponse:
    """Get paginated events for a specific family."""
    logger.info(
        "Family events request started",
        extra={"operation": "family_events", "family_id": family_id, "page": page, "per_page": per_page},
    )
    try:
        result = event_service.get_events_by_family(db, family_id, page, per_page)
        logger.info(
            "Family events request completed",
            extra={"operation": "family_events", "family_id": family_id, "result_count": len(result['events'])},
        )
        return EventListResponse(**result)
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        _log_route_error("family_events", exc, family_id=family_id, page=page, per_page=per_page)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: DbSession) -> EventResponse:
    """Get a specific event by ID."""
    logger.info("Get event request started", extra={"operation": "get_event", "event_id": event_id})
    try:
        event = cast(EventResponse, event_service.get_event_by_id(db, event_id))
        logger.info("Get event request completed", extra={"operation": "get_event", "event_id": event_id})
        return event
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        _log_route_error("get_event", exc, event_id=event_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event: EventUpdate, db: DbSession) -> EventResponse:
    """Update an event (partial update supported)."""
    logger.info("Update event request started", extra={"operation": "update_event", "event_id": event_id})
    try:
        updated = cast(EventResponse, event_service.update_event(db, event_id, event))
        logger.info("Update event request completed", extra={"operation": "update_event", "event_id": event_id})
        return updated
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        _log_route_error("update_event", exc, event_id=event_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/{event_id}")
def delete_event(event_id: int, db: DbSession) -> dict[str, str]:
    """Delete an event."""
    logger.info("Delete event request started", extra={"operation": "delete_event", "event_id": event_id})
    try:
        result = event_service.delete_event(db, event_id)
        logger.info("Delete event request completed", extra={"operation": "delete_event", "event_id": event_id})
        return result
    except CalendarAPIException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        _log_route_error("delete_event", exc, event_id=event_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
