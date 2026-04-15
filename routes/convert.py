import logging

from fastapi import APIRouter, HTTPException, Query

from exceptions import CalendarAPIException
from models.event import DateConversionResponse, SimpleDate
from services.date_service import (
    convert_to_gregorian,
    convert_to_hebrew,
    get_today_dates,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/convert/hebrew", response_model=DateConversionResponse)
def to_hebrew(
    year: int = Query(..., description="Gregorian year", ge=1, le=9999),
    month: int = Query(..., description="Gregorian month", ge=1, le=12),
    day: int = Query(..., description="Gregorian day", ge=1, le=31),
) -> DateConversionResponse:
    """Convert Gregorian date to Hebrew date.

    Example: /convert/hebrew?year=2026&month=2&day=28
    """
    logger.info(
        "Date conversion request started",
        extra={"operation": "convert_to_hebrew", "year": year, "month": month, "day": day},
    )
    try:
        h_year, h_month, h_day = convert_to_hebrew(year, month, day)
        response = DateConversionResponse(
            gregorian_date=SimpleDate(year=year, month=month, day=day),
            hebrew_date=SimpleDate(year=h_year, month=h_month, day=h_day),
        )
        logger.info("Date conversion request completed", extra={"operation": "convert_to_hebrew"})
        return response

    except CalendarAPIException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "details": exc.details},
        ) from exc
    except Exception as exc:
        logger.error(
            "Date conversion request failed",
            exc_info=True,
            extra={"operation": "convert_to_hebrew"},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/convert/gregorian", response_model=DateConversionResponse)
def to_gregorian(
    year: int = Query(..., description="Hebrew year", ge=1),
    month: int = Query(..., description="Hebrew month", ge=1, le=13),
    day: int = Query(..., description="Hebrew day", ge=1, le=31),
) -> DateConversionResponse:
    """Convert Hebrew date to Gregorian date.

    Example: /convert/gregorian?year=5786&month=12&day=12
    """
    logger.info(
        "Date conversion request started",
        extra={"operation": "convert_to_gregorian", "year": year, "month": month, "day": day},
    )
    try:
        g_year, g_month, g_day = convert_to_gregorian(year, month, day)
        response = DateConversionResponse(
            gregorian_date=SimpleDate(year=g_year, month=g_month, day=g_day),
            hebrew_date=SimpleDate(year=year, month=month, day=day),
        )
        logger.info("Date conversion request completed", extra={"operation": "convert_to_gregorian"})
        return response
    except CalendarAPIException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "details": exc.details},
        ) from exc
    except Exception as exc:
        logger.error(
            "Date conversion request failed",
            exc_info=True,
            extra={"operation": "convert_to_gregorian"},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/convert/today", response_model=DateConversionResponse)
def get_today() -> DateConversionResponse:
    """Get today's date in both Gregorian and Hebrew formats.

    Example: /convert/today
    """
    logger.info("Date conversion request started", extra={"operation": "get_today_dates"})
    try:
        response = get_today_dates()
        logger.info("Date conversion request completed", extra={"operation": "get_today_dates"})
        return response
    except CalendarAPIException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "details": exc.details},
        ) from exc
    except Exception as exc:
        logger.error(
            "Date conversion request failed",
            exc_info=True,
            extra={"operation": "get_today_dates"},
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc
