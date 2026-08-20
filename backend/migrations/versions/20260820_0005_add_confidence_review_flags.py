"""Add confidence review decisions.

Revision ID: 20260820_0005
Revises: 20260820_0004
Create Date: 2026-08-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0005"
down_revision: Union[str, Sequence[str], None] = "20260820_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "extracted_fields",
        sa.Column(
            "needs_review",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "extracted_fields",
        sa.Column("review_reason", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_extracted_fields_needs_review",
        "extracted_fields",
        ["needs_review"],
    )


def downgrade() -> None:
    op.drop_index("ix_extracted_fields_needs_review", table_name="extracted_fields")
    op.drop_column("extracted_fields", "review_reason")
    op.drop_column("extracted_fields", "needs_review")
