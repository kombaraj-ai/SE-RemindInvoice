"""Subscription service — plan limit enforcement and Dodo Payments integration."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import AppException
from app.models.user import User
from app.schemas.subscription import PLAN_LIMITS

logger = logging.getLogger(__name__)

_DODO_API_URL = "https://api.dodopayments.com"
_PLAN_PRODUCT_IDS: dict[str, str] = {}  # populated from settings at call time


# ---------------------------------------------------------------------------
# Invoice limit helpers
# ---------------------------------------------------------------------------

def get_current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def reset_monthly_count_if_needed(db: Session, user: User) -> None:
    """Reset the user's monthly invoice counter when the calendar month rolls over."""
    current_month = get_current_month()
    if user.plan_reset_month != current_month:
        user.monthly_invoice_count = 0
        user.plan_reset_month = current_month
        db.commit()


def check_invoice_limit(db: Session, user: User) -> None:
    """
    Raise a 403 AppException if the user has reached their monthly invoice limit.
    Also resets the counter at the start of a new month.
    """
    reset_monthly_count_if_needed(db, user)

    plan = user.plan or "free"

    # Downgrade to free if paid plan has expired
    if plan != "free" and user.plan_expires_at:
        if user.plan_expires_at < datetime.now(timezone.utc):
            user.plan = "free"
            db.commit()
            plan = "free"

    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    if user.monthly_invoice_count >= limit:
        raise AppException(
            status_code=403,
            message=(
                f"Monthly invoice limit of {limit} reached for the {plan.title()} plan. "
                "Please upgrade to create more invoices."
            ),
        )


def increment_invoice_count(db: Session, user: User) -> None:
    user.monthly_invoice_count = (user.monthly_invoice_count or 0) + 1
    db.commit()


def get_plan_status(user: User) -> dict:
    plan = user.plan or "free"
    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    count = user.monthly_invoice_count or 0
    return {
        "plan": plan,
        "monthly_invoice_count": count,
        "monthly_invoice_limit": limit,
        "invoices_remaining": max(0, limit - count),
        "plan_expires_at": user.plan_expires_at,
    }


# ---------------------------------------------------------------------------
# Dodo Payments integration
# ---------------------------------------------------------------------------

_PLAN_NAMES = {"silver": "Silver Plan", "gold": "Gold Plan"}
_PLAN_PRICES_PAISE = {"silver": 500, "gold": 1000}   # ₹5 = 500 paise, ₹10 = 1000


async def create_checkout_session(user: User, plan: str) -> str:
    """
    Create a Dodo Payments payment session and return the hosted payment URL.
    Raises AppException if the API key is missing or the API call fails.
    """
    if not settings.DODO_API_KEY:
        raise AppException(
            status_code=503,
            message="Payment processing is not configured. Please contact support.",
        )

    product_id = (
        settings.DODO_PRODUCT_ID_SILVER if plan == "silver"
        else settings.DODO_PRODUCT_ID_GOLD
    )
    if not product_id:
        raise AppException(
            status_code=503,
            message="Payment product not configured. Please contact support.",
        )

    headers = {
        "Authorization": f"Bearer {settings.DODO_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "customer": {
            "email": user.email,
            "name": user.full_name or user.email,
        },
        "product_cart": [{"product_id": product_id, "quantity": 1}],
        "metadata": {"user_id": str(user.id), "plan": plan},
        "return_url": f"{settings.FRONTEND_URL}/settings?payment=success&plan={plan}",
        "payment_link": True,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{_DODO_API_URL}/payments",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            url = data.get("payment_link") or data.get("url") or data.get("checkout_url")
            if not url:
                raise AppException(status_code=502, message="No payment URL returned from provider.")
            logger.info("Checkout session created for user %s plan=%s", user.id, plan)
            return url
    except httpx.HTTPStatusError as exc:
        logger.error("Dodo Payments API error: %s %s", exc.response.status_code, exc.response.text)
        raise AppException(status_code=502, message="Payment provider error. Please try again.")
    except httpx.RequestError as exc:
        logger.error("Dodo Payments connection error: %s", exc)
        raise AppException(status_code=503, message="Could not reach payment provider. Please try again.")


def verify_webhook_signature(payload_bytes: bytes, signature: str) -> bool:
    """Verify a Dodo Payments webhook HMAC-SHA256 signature."""
    if not settings.DODO_WEBHOOK_SECRET:
        logger.warning("DODO_WEBHOOK_SECRET not set — skipping signature verification")
        return True
    expected = hmac.new(
        settings.DODO_WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def handle_payment_webhook(db: Session, event_type: str, data: dict) -> None:
    """Process a Dodo Payments webhook event and upgrade the user's plan."""
    if event_type not in ("payment.succeeded", "payment.completed"):
        logger.debug("Ignored webhook event: %s", event_type)
        return

    metadata = data.get("metadata") or {}
    user_id = metadata.get("user_id")
    plan = metadata.get("plan")

    if not user_id or plan not in ("silver", "gold"):
        logger.warning("Webhook missing user_id or invalid plan: %s", metadata)
        return

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        logger.error("Webhook: user %s not found", user_id)
        return

    user.plan = plan
    user.plan_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    db.commit()
    logger.info("Upgraded user %s to plan=%s expires=%s", user.id, plan, user.plan_expires_at)
