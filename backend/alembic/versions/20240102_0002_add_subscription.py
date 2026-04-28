"""Add subscription plan fields to users

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("plan", sa.String(20), nullable=False, server_default="free"))
    op.add_column("users", sa.Column("monthly_invoice_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("plan_reset_month", sa.String(7), nullable=True))
    op.add_column("users", sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "plan_expires_at")
    op.drop_column("users", "plan_reset_month")
    op.drop_column("users", "monthly_invoice_count")
    op.drop_column("users", "plan")
