"""
Pydantic schemas for the Client resource.

ClientCreate     — payload for POST /clients
ClientUpdate     — payload for PUT /clients/{id}  (all fields optional)
ClientResponse   — standard list / write response
ClientDetailResponse — GET /clients/{id} with aggregated invoice stats
ClientListResponse   — paginated list wrapper
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "US"
    payment_terms_days: int = 30
    currency: str = "USD"
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    payment_terms_days: Optional[int] = None
    currency: Optional[str] = None
    notes: Optional[str] = None


class ClientResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    phone: Optional[str]
    company_name: Optional[str]
    address_line1: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: str
    payment_terms_days: int
    currency: str
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ClientListResponse(BaseModel):
    items: list[ClientResponse]
    total: int


class ClientDetailResponse(ClientResponse):
    """ClientResponse extended with aggregated invoice summary fields."""

    total_invoiced: float = 0.0
    total_paid: float = 0.0
    outstanding: float = 0.0
    invoice_count: int = 0
