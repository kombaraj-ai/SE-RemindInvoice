"""
Base mixins for SQLAlchemy models.
Provides reusable timestamp and soft-delete functionality.
"""

from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.sql import func


class TimestampMixin:
    """Adds created_at and updated_at columns to any model."""

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )


class SoftDeleteMixin:
    """Adds soft-delete support: is_deleted flag and deleted_at timestamp."""

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
