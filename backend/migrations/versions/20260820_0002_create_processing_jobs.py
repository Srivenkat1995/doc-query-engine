"""Create processing jobs table.

Revision ID: 20260820_0002
Revises: 20260820_0001
Create Date: 2026-08-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0002"
down_revision: Union[str, Sequence[str], None] = "20260820_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "invoice_id",
            "idempotency_key",
            name="uq_processing_jobs_invoice_idempotency_key",
        ),
    )
    op.create_index(
        "ix_processing_jobs_invoice_id",
        "processing_jobs",
        ["invoice_id"],
        unique=False,
    )
    op.create_index(
        "ix_processing_jobs_status",
        "processing_jobs",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_processing_jobs_status", table_name="processing_jobs")
    op.drop_index("ix_processing_jobs_invoice_id", table_name="processing_jobs")
    op.drop_table("processing_jobs")