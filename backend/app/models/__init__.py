"""
Models package.

All model classes are imported here so that:
  1. Alembic's autogenerate can discover every table via Base.metadata.
  2. Application code can use `from app.models import User, Invoice, ...` directly.

Import order matters — models with foreign keys must be imported after their
target tables are registered with the Base metadata. The order below is safe.
"""

# Foundation
from app.models.base import SoftDeleteMixin, TimestampMixin  # noqa: F401

# Auth
from app.models.user import RefreshToken, User  # noqa: F401

# Core business objects (Client references User)
from app.models.client import Client  # noqa: F401

# Invoicing (Invoice references User + Client; InvoiceItem references Invoice)
from app.models.invoice import Invoice, InvoiceItem, InvoiceStatus  # noqa: F401

# Reminders (ReminderRule references User; ReminderLog references Invoice + ReminderRule)
from app.models.reminder import ReminderLog, ReminderRule, ReminderStatus, TriggerType  # noqa: F401

# Admin (AdminLog references User)
from app.models.admin import AdminLog  # noqa: F401

__all__ = [
    # Mixins
    "TimestampMixin",
    "SoftDeleteMixin",
    # Auth
    "User",
    "RefreshToken",
    # Clients
    "Client",
    # Invoices
    "Invoice",
    "InvoiceItem",
    "InvoiceStatus",
    # Reminders
    "ReminderRule",
    "ReminderLog",
    "TriggerType",
    "ReminderStatus",
    # Admin
    "AdminLog",
]
