"""
REST API router for Dashboard endpoints.

All endpoints require a valid bearer token (get_current_user dependency) and
return data scoped exclusively to the authenticated user.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Return headline financial statistics for the authenticated user.

    Includes total billed (non-cancelled invoices), total paid, outstanding
    balance, number of overdue invoices, and number of active clients.
    """
    total_billed = db.query(
        func.coalesce(func.sum(Invoice.total), 0)
    ).filter(
        Invoice.user_id == current_user.id,
        Invoice.status != InvoiceStatus.cancelled,
    ).scalar()

    total_paid = db.query(
        func.coalesce(func.sum(Invoice.total), 0)
    ).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == InvoiceStatus.paid,
    ).scalar()

    overdue_count = db.query(
        func.count(Invoice.id)
    ).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == InvoiceStatus.overdue,
    ).scalar()

    total_clients = db.query(
        func.count(Client.id)
    ).filter(
        Client.user_id == current_user.id,
        Client.is_active == True,  # noqa: E712
    ).scalar()

    total_billed_f = float(total_billed)
    total_paid_f = float(total_paid)

    logger.debug(
        "Dashboard stats for user %d: billed=%.2f paid=%.2f overdue=%d clients=%d",
        current_user.id,
        total_billed_f,
        total_paid_f,
        overdue_count,
        total_clients,
    )

    return {
        "total_billed": total_billed_f,
        "total_paid": total_paid_f,
        "outstanding": total_billed_f - total_paid_f,
        "overdue_count": overdue_count,
        "total_clients": total_clients,
    }


# ---------------------------------------------------------------------------
# Recent invoices
# ---------------------------------------------------------------------------


@router.get("/recent-invoices")
async def get_recent_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return the 5 most recently created invoices for the authenticated user."""
    invoices = (
        db.query(Invoice)
        .options(joinedload(Invoice.client))
        .filter(Invoice.user_id == current_user.id)
        .order_by(Invoice.created_at.desc())
        .limit(5)
        .all()
    )
    return {"items": invoices}


# ---------------------------------------------------------------------------
# Revenue chart
# ---------------------------------------------------------------------------


@router.get("/revenue-chart")
async def get_revenue_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Return monthly revenue totals for the last 12 months.

    Only paid invoices with a non-null paid_at timestamp are included.
    Results are grouped by calendar month and ordered chronologically.
    """
    results = (
        db.query(
            func.to_char(Invoice.paid_at, "YYYY-MM").label("month"),
            func.coalesce(func.sum(Invoice.total), 0).label("revenue"),
        )
        .filter(
            Invoice.user_id == current_user.id,
            Invoice.status == InvoiceStatus.paid,
            Invoice.paid_at.isnot(None),
            Invoice.paid_at >= func.now() - text("INTERVAL '12 months'"),
        )
        .group_by("month")
        .order_by("month")
        .all()
    )

    return {
        "data": [
            {"month": row.month, "revenue": float(row.revenue)}
            for row in results
        ]
    }


# ---------------------------------------------------------------------------
# Overdue invoices
# ---------------------------------------------------------------------------


@router.get("/overdue")
async def get_overdue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Return all overdue invoices for the authenticated user, ordered by due date
    (oldest overdue first).
    """
    invoices = (
        db.query(Invoice)
        .options(joinedload(Invoice.client))
        .filter(
            Invoice.user_id == current_user.id,
            Invoice.status == InvoiceStatus.overdue,
        )
        .order_by(Invoice.due_date)
        .all()
    )
    return {"items": invoices, "total": len(invoices)}
