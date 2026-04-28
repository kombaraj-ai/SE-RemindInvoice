"""
AdminLog model.

Immutable audit trail of every action performed through the admin panel.
Each record captures who did what, to which object, and any structured metadata.
"""

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AdminLog(Base):
    """
    Append-only audit log for admin operations.

    target_type  — the name of the resource affected (e.g. "user", "invoice").
    target_id    — the PK of the affected resource (nullable for non-row actions).
    metadata     — arbitrary JSON payload for contextual details.
    """

    __tablename__ = "admin_logs"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # ------------------------------------------------------------------
    # Actor
    # ------------------------------------------------------------------
    admin_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Action description
    # ------------------------------------------------------------------
    action = Column(String(200), nullable=False, index=True)
    target_type = Column(String(100), nullable=True, index=True)
    target_id = Column(Integer, nullable=True)

    # ------------------------------------------------------------------
    # Structured context
    # ------------------------------------------------------------------
    extra_data = Column("metadata", JSON, nullable=True)

    # ------------------------------------------------------------------
    # Audit timestamp (write-once — no updated_at)
    # ------------------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    admin_user = relationship(
        "User",
        back_populates="admin_logs",
        foreign_keys=[admin_user_id],
    )

    __table_args__ = (
        Index("ix_admin_logs_admin_action", "admin_user_id", "action"),
        Index("ix_admin_logs_target", "target_type", "target_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<AdminLog id={self.id} admin_user_id={self.admin_user_id} "
            f"action={self.action!r} target={self.target_type}:{self.target_id}>"
        )
