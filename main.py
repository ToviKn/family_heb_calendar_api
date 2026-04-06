import logging
import os
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from exceptions import CalendarAPIException
from logging_config import configure_logging, reset_request_id, set_request_id
from routes import auth, convert, events, families, notifications, users
from storage.database import Base, engine
from storage.schema_migrations import run_safe_schema_migrations

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
    try:
        Base.metadata.create_all(bind=engine)
        run_safe_schema_migrations(engine)
        logger.info("Database tables created successfully")
    except Exception as exc:
        logger.error(
            "Failed to create database tables",
            exc_info=True,
            extra={"error": str(exc)},
        )
        raise

    yield  # application runs here

app = FastAPI(
    title="Family Calendar API",
    description="A calendar API supporting both Hebrew and Gregorian dates",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    token = set_request_id(request_id)

    start_time = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"

    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "HTTP request completed",
            extra={
                "http_method": request.method,
                "request_path": request.url.path,
                "status_code": response.status_code,
                "execution_time_ms": round(duration_ms, 2),
                "client_ip": client_ip,
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response
    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            "HTTP request failed",
            exc_info=True,
            extra={
                "http_method": request.method,
                "request_path": request.url.path,
                "status_code": 500,
                "execution_time_ms": round(duration_ms, 2),
                "client_ip": client_ip,
            },
        )
        raise
    finally:
        reset_request_id(token)


# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(convert.router, tags=["Date Conversion"])
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(families.router)
app.include_router(notifications.router)

logger.info("Application startup complete")

@app.exception_handler(CalendarAPIException)
async def calendar_api_exception_handler(
    request: Request, exc: CalendarAPIException
) -> JSONResponse:
    logger.warning(
        "Calendar API exception",
        extra={
            "request_path": request.url.path,
            "status_code": exc.status_code,
            "error_type": exc.__class__.__name__,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__,
            "request_id": getattr(request.state, "request_id", "-"),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    level = logging.WARNING if exc.status_code in (401, 403) else logging.INFO
    logger.log(
        level,
        "HTTP exception raised",
        extra={
            "request_path": request.url.path,
            "status_code": exc.status_code,
            "error_type": "HTTPException",
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "type": "HTTPException",
            "request_id": getattr(request.state, "request_id", "-"),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception",
        exc_info=True,
        extra={
            "request_path": request.url.path,
            "error_type": exc.__class__.__name__,
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "message": "An unexpected error occurred.",
            "type": "InternalServerError",
            "request_id": getattr(request.state, "request_id", "-"),
        },
    )

@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Family Calendar API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "healthy",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "family-calendar-api"}
