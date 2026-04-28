"""
User and RefreshToken models.

User  — core identity record; supports both email/password and OAuth logins.
RefreshToken — persisted JWT refresh tokens; cascade-deleted with the user.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """Platform user — freelancer or admin."""

    __tablename__ = "users"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # null for OAuth-only users
    full_name = Column(String(100), nullable=True)

    # ------------------------------------------------------------------
    # Flags
    # ------------------------------------------------------------------
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # ------------------------------------------------------------------
    # OAuth
    # ------------------------------------------------------------------
    oauth_provider = Column(String(50), nullable=True)  # e.g. "google"
    avatar_url = Column(String(500), nullable=True)

    # ------------------------------------------------------------------
    # Subscription / plan
    # ------------------------------------------------------------------
    plan = Column(String(20), default="free", nullable=False, server_default="free")
    monthly_invoice_count = Column(Integer, default=0, nullable=False, server_default="0")
    plan_reset_month = Column(String(7), nullable=True)   # "YYYY-MM"
    plan_expires_at = Column(DateTime(timezone=True), nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    clients = relationship(
        "Client",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    invoices = relationship(
        "Invoice",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reminder_rules = relationship(
        "ReminderRule",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    admin_logs = relationship(
        "AdminLog",
        back_populates="admin_user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="AdminLog.admin_user_id",
    )

    # ------------------------------------------------------------------
    # Composite indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_users_email_is_active", "email", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class RefreshToken(Base):
    """
    Persisted refresh tokens.

    Tokens are hashed before storage in production; the raw value is stored
    here for demonstration — BACKEND-AGENT will hash them in the auth service.
    """

    __tablename__ = "refresh_tokens"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # Foreign key
    # ------------------------------------------------------------------
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Token data
    # ------------------------------------------------------------------
    token = Column(String(512), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user_revoked", "user_id", "revoked"),
    )

    def __repr__(self) -> str:
        return f"<RefreshToken id={self.id} user_id={self.user_id} revoked={self.revoked}>"
