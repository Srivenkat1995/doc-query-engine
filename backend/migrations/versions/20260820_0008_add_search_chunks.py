"""Add searchable source chunks.

Revision ID: 20260820_0008
Revises: 20260820_0007
Create Date: 2026-08-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0008"
down_revision: Union[str, Sequence[str], None] = "20260820_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "search_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "invoice_id",
            "position",
            name="uq_search_chunks_invoice_position",
        ),
    )
    op.create_index("ix_search_chunks_invoice_id", "search_chunks", ["invoice_id"])


def downgrade() -> None:
    op.drop_index("ix_search_chunks_invoice_id", table_name="search_chunks")
    op.drop_table("search_chunks")
