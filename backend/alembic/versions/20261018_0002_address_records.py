"""Create persisted address records and batch jobs.

Revision ID: 20261018_0002
Revises: 20261016_0001
Create Date: 2026-10-18
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20261018_0002"
down_revision: str | None = "20261016_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "batch_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("processed_count", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_batch_jobs_status", "batch_jobs", ["status"])

    op.create_table(
        "address_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("raw_address", sa.Text(), nullable=False),
        sa.Column("normalized_address", sa.Text(), nullable=True),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("corrected_components", sa.JSON(), nullable=True),
        sa.Column("resolved_reference_ids", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("review_status", sa.String(length=20), nullable=False),
        sa.Column("reviewer_comment", sa.Text(), nullable=True),
        sa.Column("parser_version", sa.String(length=30), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("geocoding_status", sa.String(length=20), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("geocoding_display_name", sa.Text(), nullable=True),
        sa.Column("geocoding_precision", sa.String(length=20), nullable=True),
        sa.Column("geocoding_provider", sa.String(length=50), nullable=True),
        sa.Column("geocoding_osm_type", sa.String(length=20), nullable=True),
        sa.Column("geocoding_osm_id", sa.Integer(), nullable=True),
        sa.Column("geocoded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["batch_id"], ["batch_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_address_records_batch_id", "address_records", ["batch_id"])
    op.create_index("ix_address_records_external_id", "address_records", ["external_id"])
    op.create_index("ix_address_records_needs_review", "address_records", ["needs_review"])
    op.create_index("ix_address_records_review_status", "address_records", ["review_status"])
    op.create_index(
        "ix_address_records_geocoding_status", "address_records", ["geocoding_status"]
    )
    op.create_index(
        "ix_address_records_batch_sequence", "address_records", ["batch_id", "sequence"]
    )
    op.create_index(
        "ix_address_records_review_queue",
        "address_records",
        ["needs_review", "review_status"],
    )


def downgrade() -> None:
    op.drop_table("address_records")
    op.drop_table("batch_jobs")
