"""
Business logic for the Client resource.

All functions accept an explicit user_id so that every database query is
scoped to the authenticated user — no cross-user data leakage is possible.
"""

import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, NotFoundError
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus
from app.schemas.client import ClientCreate, ClientUpdate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------


def get_clients(
    db: Session,
    user_id: int,
    search: str | None = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Client], int]:
    """Return a page of clients owned by *user_id*, plus the total count."""
    q = db.query(Client).filter(Client.user_id == user_id)

    if active_only:
        q = q.filter(Client.is_active == True)  # noqa: E712

    if search:
        pattern = f"%{search}%"
        q = q.filter(
            Client.name.ilike(pattern) | Client.email.ilike(pattern)
        )

    total = q.count()
    items = q.order_by(Client.name).offset(skip).limit(limit).all()
    return items, total


def get_client(db: Session, client_id: int, user_id: int) -> Client:
    """Return a single client, raising NotFoundError when absent or not owned."""
    client = (
        db.query(Client)
        .filter(Client.id == client_id, Client.user_id == user_id)
        .first()
    )
    if not client:
        raise NotFoundError("Client")
    return client


def get_client_with_stats(db: Session, client_id: int, user_id: int) -> dict:
    """Return client fields merged with aggregated invoice statistics."""
    client = get_client(db, client_id, user_id)

    stats = (
        db.query(
            func.count(Invoice.id).label("invoice_count"),
            func.coalesce(func.sum(Invoice.total), 0).label("total_invoiced"),
            func.coalesce(
                func.sum(Invoice.total).filter(
                    Invoice.status == InvoiceStatus.paid
                ),
                0,
            ).label("total_paid"),
        )
        .filter(
            Invoice.client_id == client_id,
            Invoice.user_id == user_id,
        )
        .first()
    )

    total_invoiced = float(stats.total_invoiced)
    total_paid = float(stats.total_paid)

    # Build a plain dict so ClientDetailResponse can be constructed from it.
    # SQLAlchemy __dict__ contains internal state keys (_sa_instance_state)
    # that Pydantic ignores when from_attributes=True, but we strip them here
    # for clarity when the dict is passed directly.
    client_dict = {
        k: v
        for k, v in client.__dict__.items()
        if not k.startswith("_")
    }
    return {
        **client_dict,
        "invoice_count": stats.invoice_count,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "outstanding": total_invoiced - total_paid,
    }


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------


def create_client(db: Session, user_id: int, data: ClientCreate) -> Client:
    """Create and persist a new client, enforcing per-user email uniqueness."""
    existing = (
        db.query(Client)
        .filter(Client.user_id == user_id, Client.email == data.email)
        .first()
    )
    if existing:
        raise ConflictError(f"Client with email {data.email} already exists")

    client = Client(user_id=user_id, **data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    logger.info("Client created: id=%d user_id=%d", client.id, user_id)
    return client


def update_client(
    db: Session, client_id: int, user_id: int, data: ClientUpdate
) -> Client:
    """Apply partial updates to an existing client."""
    client = get_client(db, client_id, user_id)

    # Guard against stealing another client's email within the same user scope.
    if data.email and data.email != client.email:
        duplicate = (
            db.query(Client)
            .filter(
                Client.user_id == user_id,
                Client.email == data.email,
                Client.id != client_id,
            )
            .first()
        )
        if duplicate:
            raise ConflictError(f"Email {data.email} already in use")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    logger.info("Client updated: id=%d user_id=%d", client_id, user_id)
    return client


def delete_client(db: Session, client_id: int, user_id: int) -> None:
    """
    Soft-delete a client by setting is_active=False.

    Raises ConflictError when the client has invoices that are not cancelled,
    preventing orphaned financial records.
    """
    client = get_client(db, client_id, user_id)

    active_invoices = (
        db.query(Invoice)
        .filter(
            Invoice.client_id == client_id,
            Invoice.status != InvoiceStatus.cancelled,
        )
        .count()
    )
    if active_invoices > 0:
        raise ConflictError("Cannot delete client with active invoices")

    client.is_active = False
    db.commit()
    logger.info("Client soft-deleted: id=%d user_id=%d", client_id, user_id)


def get_client_invoices(
    db: Session,
    client_id: int,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
) -> list[Invoice]:
    """Return invoices for a client, verifying ownership first."""
    get_client(db, client_id, user_id)  # raises NotFoundError if not owned

    return (
        db.query(Invoice)
        .filter(
            Invoice.client_id == client_id,
            Invoice.user_id == user_id,
        )
        .order_by(Invoice.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
