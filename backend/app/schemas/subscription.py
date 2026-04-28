"""Pydantic schemas for subscription / plan endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Plan constants (single source of truth)
# ---------------------------------------------------------------------------

PLAN_LIMITS: dict[str, int] = {
    "free": 5,
    "silver": 50,
    "gold": 100,
}

PLAN_PRICES_INR: dict[str, int] = {
    "free": 0,
    "silver": 5,
    "gold": 10,
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PlanStatusResponse(BaseModel):
    plan: str
    monthly_invoice_count: int
    monthly_invoice_limit: int
    invoices_remaining: int
    plan_expires_at: Optional[datetime]

    model_config = {"from_attributes": True}


class CheckoutRequest(BaseModel):
    plan: Literal["silver", "gold"]


class CheckoutResponse(BaseModel):
    payment_url: str
    plan: str
