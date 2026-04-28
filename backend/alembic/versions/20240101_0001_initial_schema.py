"""Initial schema — create all tables

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

Creates:
  - users
  - refresh_tokens
  - clients
  - invoices
  - invoice_items
  - reminder_rules
  - reminder_logs
  - admin_logs
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("oauth_provider", sa.String(length=50), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_email_is_active", "users", ["email", "is_active"])

    # ------------------------------------------------------------------
    # refresh_tokens
    # ------------------------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"], unique=True)
    op.create_index(
        "ix_refresh_tokens_user_revoked", "refresh_tokens", ["user_id", "revoked"]
    )

    # ------------------------------------------------------------------
    # clients
    # ------------------------------------------------------------------
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("company_name", sa.String(length=200), nullable=True),
        sa.Column("address_line1", sa.String(length=255), nullable=True),
        sa.Column("address_line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=10), nullable=False, server_default="US"),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "email", name="uq_clients_user_email"),
    )
    op.create_index("ix_clients_id", "clients", ["id"])
    op.create_index("ix_clients_user_id", "clients", ["user_id"])
    op.create_index("ix_clients_email", "clients", ["email"])
    op.create_index("ix_clients_user_is_active", "clients", ["user_id", "is_active"])

    # ------------------------------------------------------------------
    # Enums (PostgreSQL native types) — idempotent via exception handler
    # ------------------------------------------------------------------
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE invoice_status AS ENUM ('draft', 'sent', 'viewed', 'paid', 'overdue', 'cancelled');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    # ------------------------------------------------------------------
    # invoices
    # ------------------------------------------------------------------
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            PgEnum("draft", "sent", "viewed", "paid", "overdue", "cancelled",
                   name="invoice_status", create_type=False),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("pdf_url", sa.String(length=500), nullable=True),
        sa.Column("public_token", sa.String(length=36), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoices_id", "invoices", ["id"])
    op.create_index("ix_invoices_user_id", "invoices", ["user_id"])
    op.create_index("ix_invoices_client_id", "invoices", ["client_id"])
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"])
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_due_date", "invoices", ["due_date"])
    op.create_index("ix_invoices_public_token", "invoices", ["public_token"], unique=True)
    op.create_index(
        "uq_invoices_user_number", "invoices", ["user_id", "invoice_number"], unique=True
    )
    op.create_index(
        "ix_invoices_status_due_date", "invoices", ["status", "due_date"]
    )
    op.create_index(
        "ix_invoices_client_status", "invoices", ["client_id", "status"]
    )

    # ------------------------------------------------------------------
    # invoice_items
    # ------------------------------------------------------------------
    op.create_table(
        "invoice_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("quantity", sa.Numeric(8, 2), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_items_id", "invoice_items", ["id"])
    op.create_index("ix_invoice_items_invoice_id", "invoice_items", ["invoice_id"])
    op.create_index(
        "ix_invoice_items_invoice_sort", "invoice_items", ["invoice_id", "sort_order"]
    )

    # ------------------------------------------------------------------
    # Enums — reminder types
    # ------------------------------------------------------------------
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE trigger_type AS ENUM ('before_due', 'on_due', 'after_due');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE reminder_status AS ENUM ('sent', 'failed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """)

    # ------------------------------------------------------------------
    # reminder_rules
    # ------------------------------------------------------------------
    op.create_table(
        "reminder_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "trigger_type",
            PgEnum("before_due", "on_due", "after_due", name="trigger_type", create_type=False),
            nullable=False,
        ),
        sa.Column("days_offset", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reminder_rules_id", "reminder_rules", ["id"])
    op.create_index("ix_reminder_rules_user_id", "reminder_rules", ["user_id"])
    op.create_index(
        "ix_reminder_rules_user_active", "reminder_rules", ["user_id", "is_active"]
    )

    # ------------------------------------------------------------------
    # reminder_logs
    # ------------------------------------------------------------------
    op.create_table(
        "reminder_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=True),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "status",
            PgEnum("sent", "failed", name="reminder_status", create_type=False),
            nullable=False,
        ),
        sa.Column("email_to", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["reminder_rules.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reminder_logs_id", "reminder_logs", ["id"])
    op.create_index("ix_reminder_logs_invoice_id", "reminder_logs", ["invoice_id"])
    op.create_index("ix_reminder_logs_rule_id", "reminder_logs", ["rule_id"])
    op.create_index("ix_reminder_logs_status", "reminder_logs", ["status"])
    op.create_index(
        "ix_reminder_logs_invoice_status", "reminder_logs", ["invoice_id", "status"]
    )

    # ------------------------------------------------------------------
    # admin_logs
    # ------------------------------------------------------------------
    op.create_table(
        "admin_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=200), nullable=False),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["admin_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_logs_id", "admin_logs", ["id"])
    op.create_index("ix_admin_logs_admin_user_id", "admin_logs", ["admin_user_id"])
    op.create_index("ix_admin_logs_action", "admin_logs", ["action"])
    op.create_index("ix_admin_logs_target_type", "admin_logs", ["target_type"])
    op.create_index("ix_admin_logs_created_at", "admin_logs", ["created_at"])
    op.create_index(
        "ix_admin_logs_admin_action", "admin_logs", ["admin_user_id", "action"]
    )
    op.create_index(
        "ix_admin_logs_target", "admin_logs", ["target_type", "target_id"]
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("admin_logs")
    op.drop_table("reminder_logs")
    op.drop_table("reminder_rules")
    op.drop_table("invoice_items")
    op.drop_table("invoices")
    op.drop_table("clients")
    op.drop_table("refresh_tokens")
    op.drop_table("users")

    # Drop custom enum types
    op.execute("DROP TYPE IF EXISTS reminder_status")
    op.execute("DROP TYPE IF EXISTS trigger_type")
    op.execute("DROP TYPE IF EXISTS invoice_status")
