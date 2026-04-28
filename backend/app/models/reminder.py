"""
ReminderRule and ReminderLog models.

ReminderRule — user-defined rule that triggers a reminder email relative to
               an invoice's due date (before, on, or after).
ReminderLog  — audit record of every reminder email attempt (sent or failed).
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.base import TimestampMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TriggerType(str, enum.Enum):
    """When a reminder fires relative to the invoice due date."""

    before_due = "before_due"
    on_due = "on_due"
    after_due = "after_due"


class ReminderStatus(str, enum.Enum):
    """Outcome of a reminder send attempt."""

    sent = "sent"
    failed = "failed"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ReminderRule(Base, TimestampMixin):
    """
    A user-configured rule that schedules automatic reminder emails.

    Examples:
        name="3 days before due", trigger_type=before_due, days_offset=3
        name="On due date",       trigger_type=on_due,     days_offset=0
        name="1 week overdue",    trigger_type=after_due,  days_offset=7
    """

    __tablename__ = "reminder_rules"

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
    # Rule definition
    # ------------------------------------------------------------------
    name = Column(String(200), nullable=False)
    trigger_type = Column(
        Enum(TriggerType, name="trigger_type"),
        nullable=False,
    )
    days_offset = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user = relationship("User", back_populates="reminder_rules")
    logs = relationship(
        "ReminderLog",
        back_populates="rule",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_reminder_rules_user_active", "user_id", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<ReminderRule id={self.id} name={self.name!r} "
            f"trigger={self.trigger_type} offset={self.days_offset}>"
        )


class ReminderLog(Base):
    """
    Immutable record of a reminder email delivery attempt.

    rule_id is nullable — null means the reminder was triggered manually
    rather than by an automated ReminderRule.
    """

    __tablename__ = "reminder_logs"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # ------------------------------------------------------------------
    # Foreign keys
    # ------------------------------------------------------------------
    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id = Column(
        Integer,
        ForeignKey("reminder_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Delivery details
    # ------------------------------------------------------------------
    sent_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status = Column(
        Enum(ReminderStatus, name="reminder_status"),
        nullable=False,
        index=True,
    )
    email_to = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    error_message = Column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    invoice = relationship("Invoice", back_populates="reminder_logs")
    rule = relationship("ReminderRule", back_populates="logs")

    __table_args__ = (
        Index("ix_reminder_logs_invoice_status", "invoice_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<ReminderLog id={self.id} invoice_id={self.invoice_id} "
            f"status={self.status} email_to={self.email_to!r}>"
        )
