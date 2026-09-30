"""Private operational endpoints invoked by trusted automation only."""

import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.jobs.process_reminders import run_reminder_processing
from app.storage.database import get_db

router = APIRouter(prefix="/internal", include_in_schema=False)
logger = logging.getLogger(__name__)
DbSession = Annotated[Session, Depends(get_db)]
bearer_scheme = HTTPBearer(auto_error=False)


def require_reminder_process_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> None:
    """Authorize only the dedicated automation token, never a user JWT."""
    configured_token = settings.reminder_process_token
    provided_token = credentials.credentials if credentials and credentials.scheme.lower() == "bearer" else ""

    if not configured_token:
        logger.error("Reminder processing endpoint is not configured with a token")
        raise HTTPException(status_code=503, detail="Reminder processing is not configured.")

    if not secrets.compare_digest(provided_token, configured_token):
        raise HTTPException(status_code=401, detail="Invalid reminder processing credentials.")


@router.post("/reminders/process", dependencies=[Depends(require_reminder_process_token)])
def process_scheduled_reminders(db: DbSession) -> dict[str, int]:
    """Run the existing reminder job; this endpoint accepts no arbitrary job name."""
    created = run_reminder_processing(db)
    logger.info(
        "Reminder processing requested by trusted automation",
        extra={"created_count": created},
    )
    return {"created": created}
