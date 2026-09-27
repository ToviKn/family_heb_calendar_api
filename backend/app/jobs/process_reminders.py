"""Run event reminder evaluation from the production scheduler."""

import logging

from app.services.notification_service import process_event_reminders
from app.logging_config import configure_logging
from app.storage.database import SessionLocal

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    with SessionLocal() as db:
        created = process_event_reminders(db)
    logger.info("Scheduled event reminder processing completed", extra={"created": created})


if __name__ == "__main__":
    main()
