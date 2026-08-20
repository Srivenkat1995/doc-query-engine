"""Add structured invoice filter fields.

Revision ID: 20260820_0010
Revises: 20260820_0009
Create Date: 2026-08-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0010"
down_revision: Union[str, Sequence[str], None] = "20260820_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("vendor", sa.String(length=255), nullable=True))
    op.add_column("invoices", sa.Column("total", sa.Float(), nullable=True))
    op.add_column(
        "invoices",
        sa.Column("due_date", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_invoices_vendor", "invoices", ["vendor"])
    op.create_index("ix_invoices_total", "invoices", ["total"])
    op.create_index("ix_invoices_due_date", "invoices", ["due_date"])


def downgrade() -> None:
    op.drop_index("ix_invoices_due_date", table_name="invoices")
    op.drop_index("ix_invoices_total", table_name="invoices")
    op.drop_index("ix_invoices_vendor", table_name="invoices")
    op.drop_column("invoices", "due_date")
    op.drop_column("invoices", "total")
    op.drop_column("invoices", "vendor")