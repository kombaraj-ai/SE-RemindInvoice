"""
Invoice and InvoiceItem models.

Invoice  — the billable document sent from a User (freelancer) to a Client.
InvoiceItem — individual line items that compose an invoice's subtotal.

All monetary fields use Numeric (exact decimal arithmetic) instead of Float
to avoid floating-point rounding errors in financial calculations.
"""

import enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class InvoiceStatus(str, enum.Enum):
    """Lifecycle states of an invoice."""

    draft = "draft"
    sent = "sent"
    viewed = "viewed"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Invoice(Base, TimestampMixin):
    """
    A payable document created by a freelancer (user) for a client.

    public_token — UUID v4 stored as a plain string — lets clients view their
    invoice without authentication via GET /invoices/public/{public_token}.
    """

    __tablename__ = "invoices"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # ------------------------------------------------------------------
    # Ownership
    # ------------------------------------------------------------------
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    client_id = Column(
        Integer,
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    invoice_number = Column(String(50), nullable=False, index=True)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    status = Column(
        Enum(InvoiceStatus, name="invoice_status"),
        default=InvoiceStatus.draft,
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Dates
    # ------------------------------------------------------------------
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False, index=True)

    # ------------------------------------------------------------------
    # Financials  (Numeric = exact decimal; never Float for money)
    # ------------------------------------------------------------------
    subtotal = Column(Numeric(10, 2), default=0, nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total = Column(Numeric(10, 2), default=0, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------
    notes = Column(Text, nullable=True)
    pdf_url = Column(String(500), nullable=True)

    # ------------------------------------------------------------------
    # Public access token — UUID v4 as string
    # ------------------------------------------------------------------
    public_token = Column(String(36), unique=True, index=True, nullable=False)

    # ------------------------------------------------------------------
    # Lifecycle timestamps
    # ------------------------------------------------------------------
    sent_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user = relationship("User", back_populates="invoices")
    client = relationship("Client", back_populates="invoices")
    items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="InvoiceItem.sort_order",
    )
    reminder_logs = relationship(
        "ReminderLog",
        back_populates="invoice",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # ------------------------------------------------------------------
    # Composite indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        # Enforce unique invoice_number per user at the DB level
        Index("uq_invoices_user_number", "user_id", "invoice_number", unique=True),
        # Fast queries for overdue detection job (status + due_date)
        Index("ix_invoices_status_due_date", "status", "due_date"),
        # Per-client invoice listing
        Index("ix_invoices_client_status", "client_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Invoice id={self.id} number={self.invoice_number!r} "
            f"status={self.status} user_id={self.user_id}>"
        )


class InvoiceItem(Base):
    """A single line item on an invoice (description + quantity × unit_price)."""

    __tablename__ = "invoice_items"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # ------------------------------------------------------------------
    # Parent invoice
    # ------------------------------------------------------------------
    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Line item data
    # ------------------------------------------------------------------
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(8, 2), default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), default=0, nullable=False)
    amount = Column(Numeric(10, 2), default=0, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    invoice = relationship("Invoice", back_populates="items")

    __table_args__ = (
        Index("ix_invoice_items_invoice_sort", "invoice_id", "sort_order"),
    )

    def __repr__(self) -> str:
        return (
            f"<InvoiceItem id={self.id} invoice_id={self.invoice_id} "
            f"description={self.description!r} amount={self.amount}>"
        )
