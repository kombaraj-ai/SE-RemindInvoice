"""
Client model.

A Client belongs to a User (the freelancer) and represents a person or company
that receives invoices. Email must be unique per user (enforced by DB constraint).
"""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampMixin


class Client(Base, TimestampMixin):
    """Client (payer) managed by a freelancer user."""

    __tablename__ = "clients"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # ------------------------------------------------------------------
    # Owner
    # ------------------------------------------------------------------
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Contact information
    # ------------------------------------------------------------------
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    company_name = Column(String(200), nullable=True)

    # ------------------------------------------------------------------
    # Address
    # ------------------------------------------------------------------
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(10), default="US", nullable=False)

    # ------------------------------------------------------------------
    # Billing defaults
    # ------------------------------------------------------------------
    payment_terms_days = Column(Integer, default=30, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)

    # ------------------------------------------------------------------
    # Miscellaneous
    # ------------------------------------------------------------------
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user = relationship("User", back_populates="clients")
    invoices = relationship(
        "Invoice",
        back_populates="client",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        # Client email must be unique per user
        UniqueConstraint("user_id", "email", name="uq_clients_user_email"),
        # Composite index to speed up per-user active-client queries
        Index("ix_clients_user_is_active", "user_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Client id={self.id} name={self.name!r} user_id={self.user_id}>"
