"""Add invoice review issues.

Revision ID: 20260820_0006
Revises: 20260820_0005
Create Date: 2026-08-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0006"
down_revision: Union[str, Sequence[str], None] = "20260820_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invoice_issues",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_issues_invoice_id", "invoice_issues", ["invoice_id"])
    op.create_index("ix_invoice_issues_code", "invoice_issues", ["code"])


def downgrade() -> None:
    op.drop_index("ix_invoice_issues_code", table_name="invoice_issues")
    op.drop_index("ix_invoice_issues_invoice_id", table_name="invoice_issues")
    op.drop_table("invoice_issues")
