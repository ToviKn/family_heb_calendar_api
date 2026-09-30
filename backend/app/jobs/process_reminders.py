"""Run the shared event reminder evaluation job."""

import logging

from sqlalchemy.orm import Session

from app.services.notification_service import process_event_reminders
from app.logging_config import configure_logging
from app.storage.database import SessionLocal

logger = logging.getLogger(__name__)


def run_reminder_processing(db: Session | None = None) -> int:
    """Evaluate reminders using either a request session or a job-owned session."""
    if db is not None:
        return process_event_reminders(db)

    with SessionLocal() as job_db:
        return process_event_reminders(job_db)


def main() -> None:
    configure_logging()
    created = run_reminder_processing()
    logger.info("Scheduled event reminder processing completed", extra={"created_count": created})


if __name__ == "__main__":
    main()
