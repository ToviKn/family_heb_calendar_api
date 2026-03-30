import logging
import os
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")
DATABASE_URL = str(DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
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
