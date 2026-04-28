"""
Pydantic schemas for Invoice and InvoiceItem request/response validation.

Schemas are intentionally kept separate from SQLAlchemy models so that
API contracts can evolve independently of the database schema.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.invoice import InvoiceStatus


# ---------------------------------------------------------------------------
# InvoiceItem schemas
# ---------------------------------------------------------------------------


class ClientBriefResponse(BaseModel):
    """Minimal client info embedded in invoice responses."""

    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    company_name: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]

    model_config = {"from_attributes": True}


class InvoiceItemCreate(BaseModel):
    """Payload for a single line item when creating or updating an invoice."""

    description: str
    quantity: Decimal
    unit_price: Decimal
    sort_order: int = 0


class InvoiceItemResponse(BaseModel):
    """Read-only representation of a persisted line item."""

    id: int
    invoice_id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    sort_order: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Invoice schemas
# ---------------------------------------------------------------------------


class InvoiceCreate(BaseModel):
    """Payload required to create a new invoice (draft)."""

    client_id: int
    issue_date: date
    due_date: date
    tax_rate: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    currency: str = "USD"
    notes: Optional[str] = None
    items: list[InvoiceItemCreate]

    @field_validator("items")
    @classmethod
    def must_have_items(cls, v: list[InvoiceItemCreate]) -> list[InvoiceItemCreate]:
        if not v:
            raise ValueError("Invoice must have at least one item")
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_after_issue_date(cls, v: date, info) -> date:  # noqa: ANN001
        issue_date = info.data.get("issue_date")
        if issue_date and v < issue_date:
            raise ValueError("due_date must not be before issue_date")
        return v

    @field_validator("tax_rate")
    @classmethod
    def tax_rate_non_negative(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("tax_rate must be non-negative")
        return v

    @field_validator("discount_amount")
    @classmethod
    def discount_non_negative(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("discount_amount must be non-negative")
        return v

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.upper()


class InvoiceUpdate(BaseModel):
    """Partial update payload — all fields are optional (draft invoices only)."""

    client_id: Optional[int] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    tax_rate: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[list[InvoiceItemCreate]] = None

    @field_validator("tax_rate")
    @classmethod
    def tax_rate_non_negative(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < Decimal("0"):
            raise ValueError("tax_rate must be non-negative")
        return v

    @field_validator("discount_amount")
    @classmethod
    def discount_non_negative(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < Decimal("0"):
            raise ValueError("discount_amount must be non-negative")
        return v

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v


class InvoiceResponse(BaseModel):
    """Full read-only representation of a persisted invoice, including its items."""

    id: int
    user_id: int
    client_id: int
    invoice_number: str
    status: InvoiceStatus
    issue_date: date
    due_date: date
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    currency: str
    notes: Optional[str]
    pdf_url: Optional[str]
    public_token: str
    sent_at: Optional[datetime]
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    items: list[InvoiceItemResponse] = []
    client: Optional[ClientBriefResponse] = None

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    """Paginated list of invoices returned by the list endpoint."""

    items: list[InvoiceResponse]
    total: int
