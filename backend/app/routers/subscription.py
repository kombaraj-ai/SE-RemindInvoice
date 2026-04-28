"""Subscription router — plan status, checkout, and webhook."""

import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import AppException, app_exception_handler
from app.models.user import User
from app.schemas.subscription import CheckoutRequest, CheckoutResponse, PlanStatusResponse
from app.services import subscription_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscription", tags=["Subscription"])


@router.get(
    "/status",
    response_model=PlanStatusResponse,
    summary="Get current plan status and usage",
)
async def plan_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlanStatusResponse:
    """Return the authenticated user's current plan, usage, and limits."""
    subscription_service.reset_monthly_count_if_needed(db, current_user)
    return PlanStatusResponse(**subscription_service.get_plan_status(current_user))


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Create a Dodo Payments checkout session",
)
async def create_checkout(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    """Return a hosted payment URL for upgrading to Silver or Gold plan."""
    try:
        url = await subscription_service.create_checkout_session(current_user, body.plan)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return CheckoutResponse(payment_url=url, plan=body.plan)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Dodo Payments webhook receiver",
)
async def dodo_webhook(
    request: Request,
    db: Session = Depends(get_db),
    dodo_signature: str | None = Header(default=None, alias="dodo-signature"),
) -> dict:
    """
    Receive and process Dodo Payments webhook events.
    Verifies the HMAC-SHA256 signature before updating the user's plan.
    """
    payload_bytes = await request.body()

    if dodo_signature and not subscription_service.verify_webhook_signature(
        payload_bytes, dodo_signature
    ):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("type") or payload.get("event_type", "")
    data = payload.get("data") or {}

    subscription_service.handle_payment_webhook(db, event_type, data)
    return {"received": True}
