"""
REST API router for Admin panel endpoints.

All endpoints require the authenticated user to have is_admin=True
(enforced via the get_admin_user dependency). Admin actions are recorded
in the admin_logs table for audit purposes.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_admin_user
from app.exceptions import NotFoundError
from app.models.admin import AdminLog
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User
from app.schemas.admin import (
    AdminLogResponse,
    AdminStats,
    AdminUserResponse,
    AdminUserStatusUpdate,
)

# ---------------------------------------------------------------------------
# Reusable aggregate subqueries — avoid N+1 queries in list/detail endpoints
# ---------------------------------------------------------------------------

def _invoice_count_subquery(db: Session):
    """Return a scalar subquery mapping user_id -> invoice count."""
    return (
        db.query(Invoice.user_id, func.count(Invoice.id).label("invoice_count"))
        .group_by(Invoice.user_id)
        .subquery()
    )


def _client_count_subquery(db: Session):
    """Return a scalar subquery mapping user_id -> client count."""
    return (
        db.query(Client.user_id, func.count(Client.id).label("client_count"))
        .group_by(Client.user_id)
        .subquery()
    )

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    search: str | None = Query(None, description="Filter by email or name (case-insensitive)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> list:
    """
    Return a paginated list of all users, optionally filtered by email or name.

    Counts are aggregated via LEFT JOINs against precomputed subqueries so the
    full list is fetched in a single round-trip (no N+1).
    """
    inv_sq = _invoice_count_subquery(db)
    cli_sq = _client_count_subquery(db)

    q = (
        db.query(
            User,
            func.coalesce(inv_sq.c.invoice_count, 0).label("invoice_count"),
            func.coalesce(cli_sq.c.client_count, 0).label("client_count"),
        )
        .outerjoin(inv_sq, User.id == inv_sq.c.user_id)
        .outerjoin(cli_sq, User.id == cli_sq.c.user_id)
    )
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            User.email.ilike(pattern) | User.full_name.ilike(pattern)
        )

    rows = q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {**user.__dict__, "invoice_count": inv_count, "client_count": cli_count}
        for user, inv_count, cli_count in rows
    ]


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> dict:
    """Return full details for a single user, including invoice and client counts."""
    inv_sq = _invoice_count_subquery(db)
    cli_sq = _client_count_subquery(db)

    row = (
        db.query(
            User,
            func.coalesce(inv_sq.c.invoice_count, 0).label("invoice_count"),
            func.coalesce(cli_sq.c.client_count, 0).label("client_count"),
        )
        .outerjoin(inv_sq, User.id == inv_sq.c.user_id)
        .outerjoin(cli_sq, User.id == cli_sq.c.user_id)
        .filter(User.id == user_id)
        .first()
    )
    if not row:
        raise NotFoundError("User")

    user, inv_count, cli_count = row
    return {**user.__dict__, "invoice_count": inv_count, "client_count": cli_count}


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    data: AdminUserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> dict:
    """
    Activate or deactivate a user account.

    The action is recorded in admin_logs with the admin's user ID and the
    new is_active value as structured metadata.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User")

    user.is_active = data.is_active
    log = AdminLog(
        admin_user_id=admin.id,
        action="update_user_status",
        target_type="user",
        target_id=user_id,
        extra_data={"is_active": data.is_active},
    )
    db.add(log)
    db.commit()

    logger.info(
        "Admin %d set user %d is_active=%s",
        admin.id,
        user_id,
        data.is_active,
    )
    return {"user_id": user_id, "is_active": data.is_active}


# ---------------------------------------------------------------------------
# Platform stats
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=AdminStats)
async def get_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> dict:
    """Return platform-wide aggregate statistics (user counts, invoices, revenue)."""
    total_revenue = db.query(
        func.coalesce(func.sum(Invoice.total), 0)
    ).filter(
        Invoice.status == InvoiceStatus.paid
    ).scalar()

    return {
        "total_users": db.query(func.count(User.id)).scalar(),
        "active_users": db.query(func.count(User.id)).filter(
            User.is_active == True  # noqa: E712
        ).scalar(),
        "total_invoices": db.query(func.count(Invoice.id)).scalar(),
        "total_revenue": float(total_revenue),
    }


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------


@router.get("/logs", response_model=list[AdminLogResponse])
async def get_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
) -> list:
    """Return paginated admin audit logs, ordered newest-first."""
    return (
        db.query(AdminLog)
        .order_by(AdminLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
