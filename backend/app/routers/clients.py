"""
REST API router for the Client resource.

All endpoints require a valid bearer token (enforced by get_current_user).
Every database query is automatically scoped to the authenticated user's id.

Prefix : /clients
Tags   : Clients
"""

import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.client import (
    ClientCreate,
    ClientDetailResponse,
    ClientListResponse,
    ClientResponse,
    ClientUpdate,
)
from app.services import client_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["Clients"])


# ---------------------------------------------------------------------------
# Collection endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ClientListResponse)
async def list_clients(
    search: str | None = Query(None, description="Filter by name or email"),
    active_only: bool = Query(True, description="Return only active clients"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClientListResponse:
    """List clients belonging to the authenticated user with optional search and pagination."""
    items, total = client_service.get_clients(
        db, current_user.id, search, active_only, skip, limit
    )
    return ClientListResponse(items=items, total=total)


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClientResponse:
    """Create a new client for the authenticated user."""
    return client_service.create_client(db, current_user.id, data)


# ---------------------------------------------------------------------------
# Item endpoints
# ---------------------------------------------------------------------------


@router.get("/{client_id}", response_model=ClientDetailResponse)
async def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClientDetailResponse:
    """Retrieve a single client with aggregated invoice statistics."""
    stats_dict = client_service.get_client_with_stats(db, client_id, current_user.id)
    return ClientDetailResponse.model_validate(stats_dict)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClientResponse:
    """Partially update a client owned by the authenticated user."""
    return client_service.update_client(db, client_id, current_user.id, data)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Soft-delete a client (sets is_active=False).

    Returns 409 Conflict when the client has non-cancelled invoices.
    """
    client_service.delete_client(db, client_id, current_user.id)


@router.get("/{client_id}/invoices")
async def get_client_invoices(
    client_id: int,
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List invoices belonging to a specific client of the authenticated user."""
    invoices = client_service.get_client_invoices(
        db, client_id, current_user.id, skip, limit
    )
    return {"items": invoices, "total": len(invoices)}
