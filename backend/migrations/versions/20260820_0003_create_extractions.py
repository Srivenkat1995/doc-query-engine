"""Create extraction result tables.

Revision ID: 20260820_0003
Revises: 20260820_0002
Create Date: 2026-08-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0003"
down_revision: Union[str, Sequence[str], None] = "20260820_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extractions",
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("invoice_id"),
    )
    op.create_table(
        "extracted_fields",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("citation_page", sa.Integer(), nullable=True),
        sa.Column("citation_text", sa.Text(), nullable=True),
        sa.Column("bounding_box", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "invoice_id",
            "name",
            name="uq_extracted_fields_invoice_name",
        ),
    )
    op.create_index(
        "ix_extracted_fields_invoice_id",
        "extracted_fields",
        ["invoice_id"],
    )
    op.create_table(
        "line_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quantity", sa.String(length=64), nullable=False),
        sa.Column("unit_price", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.String(length=64), nullable=False),
        sa.Column("citation_page", sa.Integer(), nullable=True),
        sa.Column("citation_text", sa.Text(), nullable=True),
        sa.Column("bounding_box", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_line_items_invoice_id", "line_items", ["invoice_id"])


def downgrade() -> None:
    op.drop_index("ix_line_items_invoice_id", table_name="line_items")
    op.drop_table("line_items")
    op.drop_index("ix_extracted_fields_invoice_id", table_name="extracted_fields")
    op.drop_table("extracted_fields")
    op.drop_table("extractions")
