"""
REST API router for Reminder Rules and Reminder Logs.

All endpoints require a valid bearer token (get_current_user dependency).
Reminder rules are user-scoped — users can only manage their own rules.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.reminder import (
    ReminderLogResponse,
    ReminderRuleCreate,
    ReminderRuleResponse,
    ReminderRuleUpdate,
)
from app.services import reminder_service

router = APIRouter(prefix="/reminders", tags=["Reminders"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reminder Rule endpoints
# ---------------------------------------------------------------------------


@router.get("/rules", response_model=list[ReminderRuleResponse])
async def list_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    """Return all reminder rules owned by the authenticated user."""
    return reminder_service.get_rules(db, current_user.id)


@router.post("/rules", response_model=ReminderRuleResponse, status_code=201)
async def create_rule(
    data: ReminderRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    """Create a new reminder rule for the authenticated user."""
    return reminder_service.create_rule(db, current_user.id, data)


@router.put("/rules/{rule_id}", response_model=ReminderRuleResponse)
async def update_rule(
    rule_id: int,
    data: ReminderRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    """Partially update a reminder rule. Only provided fields are changed."""
    return reminder_service.update_rule(db, rule_id, current_user.id, data)


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Permanently delete a reminder rule."""
    reminder_service.delete_rule(db, rule_id, current_user.id)


# ---------------------------------------------------------------------------
# Manual reminder send
# ---------------------------------------------------------------------------


@router.post("/send/{invoice_id}")
async def send_manual_reminder(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    """
    Immediately dispatch a one-off payment reminder for a specific invoice.

    Returns ``{"sent": true}`` when the email was accepted, ``{"sent": false}``
    when delivery failed (a ReminderLog is written in both cases).
    """
    success = reminder_service.send_manual_reminder(db, invoice_id, current_user.id)
    return {"sent": success}


# ---------------------------------------------------------------------------
# Reminder Log endpoints
# ---------------------------------------------------------------------------


@router.get("/logs", response_model=list[ReminderLogResponse])
async def get_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    """Return all reminder logs for invoices owned by the authenticated user."""
    return reminder_service.get_logs(db, current_user.id, skip=skip, limit=limit)


@router.get("/logs/{invoice_id}", response_model=list[ReminderLogResponse])
async def get_invoice_logs(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    """Return reminder logs filtered to a specific invoice."""
    return reminder_service.get_logs(db, current_user.id, invoice_id=invoice_id)
