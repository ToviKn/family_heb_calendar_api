import logging
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

from app.config import settings

DATABASE_URL = settings.database_url
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")
DATABASE_URL = str(DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    echo=settings.debug,
    poolclass=QueuePool,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=settings.db_pool_recycle_seconds,
    pool_timeout=settings.db_pool_timeout_seconds,
)

SessionLocal = sessionmaker[Session](autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


@event.listens_for(Session, "after_commit")
def log_db_commit(session: Session) -> None:
    logger.info(
        "Database transaction committed",
        extra={"operation": "db_commit", "session_id": id(session)},
    )


@event.listens_for(Session, "after_rollback")
def log_db_rollback(session: Session) -> None:
    logger.warning(
        "Database transaction rolled back",
        extra={"operation": "db_rollback", "session_id": id(session)},
    )


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
    database_url = str(DATABASE_URL)
    if "sqlite" in database_url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    logger.info(
        "Database session opened",
        extra={"operation": "db_session_opened", "session_id": id(db)},
    )
    try:
        yield db
    except Exception:
        logger.error(
            "Database session failed; rolling back",
            exc_info=True,
            extra={"operation": "db_session_failed", "session_id": id(db)},
        )
        db.rollback()
        raise
    finally:
        db.close()
        logger.info(
            "Database session closed",
            extra={"operation": "db_session_closed", "session_id": id(db)},
        )
