"""Fix reminder_rules.is_active column type from INTEGER to BOOLEAN

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-03 00:00:00.000000

The initial migration incorrectly created is_active as INTEGER. SQLAlchemy's
Boolean type sends Python True/False as PostgreSQL booleans (OID 16), which
PostgreSQL rejects for INTEGER columns — causing all INSERT operations on
reminder_rules to fail with a type error.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the integer default first — PostgreSQL refuses to alter type while
    # an incompatible column default is present.
    op.alter_column("reminder_rules", "is_active", server_default=None, existing_type=sa.Integer(), existing_nullable=False)
    op.alter_column(
        "reminder_rules",
        "is_active",
        type_=sa.Boolean(),
        postgresql_using="is_active::boolean",
        existing_nullable=False,
    )
    op.alter_column("reminder_rules", "is_active", server_default=sa.text("true"), existing_type=sa.Boolean(), existing_nullable=False)


def downgrade() -> None:
    op.alter_column("reminder_rules", "is_active", server_default=None, existing_type=sa.Boolean(), existing_nullable=False)
    op.alter_column(
        "reminder_rules",
        "is_active",
        type_=sa.Integer(),
        postgresql_using="is_active::integer",
        existing_nullable=False,
    )
    op.alter_column("reminder_rules", "is_active", server_default=sa.text("1"), existing_type=sa.Integer(), existing_nullable=False)
