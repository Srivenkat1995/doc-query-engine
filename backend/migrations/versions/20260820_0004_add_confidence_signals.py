"""Add confidence signal components.

Revision ID: 20260820_0004
Revises: 20260820_0003
Create Date: 2026-08-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0004"
down_revision: Union[str, Sequence[str], None] = "20260820_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "extracted_fields",
        sa.Column("confidence_signals", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("extracted_fields", "confidence_signals")
