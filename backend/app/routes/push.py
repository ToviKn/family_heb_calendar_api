import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.models import PushSubscription, User
from app.models.push import PushSubscriptionCreate, PushSubscriptionResponse, PushUnsubscribeRequest
from app.services.auth_service import get_current_user
from app.storage.database import get_db

router = APIRouter(prefix="/push", tags=["push"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
logger = logging.getLogger(__name__)


@router.post("/subscribe", response_model=PushSubscriptionResponse, status_code=201)
def subscribe(payload: PushSubscriptionCreate, db: DbSession, current_user: CurrentUser):
    subscription = db.query(PushSubscription).filter(PushSubscription.user_id == current_user.id, PushSubscription.endpoint == payload.endpoint).first()
    if subscription is None:
        subscription = PushSubscription(user_id=current_user.id, endpoint=payload.endpoint, p256dh_key=payload.keys.p256dh, auth_key=payload.keys.auth)
        db.add(subscription)
    else:
        subscription.p256dh_key = payload.keys.p256dh
        subscription.auth_key = payload.keys.auth
    db.commit()
    db.refresh(subscription)
    logger.info("Subscription added", extra={"operation": "push_subscribe", "user_id": current_user.id, "subscription_id": subscription.id})
    return subscription


@router.delete("/unsubscribe", status_code=204)
def unsubscribe(payload: PushUnsubscribeRequest, db: DbSession, current_user: CurrentUser) -> None:
    subscription = db.query(PushSubscription).filter(PushSubscription.user_id == current_user.id, PushSubscription.endpoint == payload.endpoint).first()
    if subscription is not None:
        db.delete(subscription)
        db.commit()
        logger.info("Subscription removed", extra={"operation": "push_unsubscribe", "user_id": current_user.id})
