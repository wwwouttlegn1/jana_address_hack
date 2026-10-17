"""Create the address reference directory.

Revision ID: 20261016_0001
Revises:
Create Date: 2026-10-16
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20261016_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "address_references",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["address_references.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint(
            "kind", "normalized_name", "parent_id", name="uq_reference_kind_name_parent"
        ),
    )
    op.create_index("ix_address_references_enabled", "address_references", ["enabled"])
    op.create_index("ix_address_references_kind", "address_references", ["kind"])
    op.create_index("ix_address_references_parent_id", "address_references", ["parent_id"])
    op.create_index(
        "ix_reference_kind_normalized",
        "address_references",
        ["kind", "normalized_name"],
    )


def downgrade() -> None:
    op.drop_table("address_references")
