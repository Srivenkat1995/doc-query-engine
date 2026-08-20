"""Add dedicated citation records.

Revision ID: 20260820_0007
Revises: 20260820_0006
Create Date: 2026-08-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0007"
down_revision: Union[str, Sequence[str], None] = "20260820_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "citation_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("bounding_box", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_citation_records_invoice_id",
        "citation_records",
        ["invoice_id"],
    )
    op.create_index(
        "ix_citation_records_entity_id",
        "citation_records",
        ["entity_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_citation_records_entity_id", table_name="citation_records")
    op.drop_index("ix_citation_records_invoice_id", table_name="citation_records")
    op.drop_table("citation_records")
