from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.database import Base


class BatchStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    corrected = "corrected"
    rejected = "rejected"


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(20), default=BatchStatus.queued.value, index=True)
    source_type: Mapped[str] = mapped_column(String(20), default="json")
    source_name: Mapped[str | None] = mapped_column(String(255))
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    records: Mapped[list[AddressRecord]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class AddressRecord(Base):
    __tablename__ = "address_records"
    __table_args__ = (
        Index("ix_address_records_batch_sequence", "batch_id", "sequence"),
        Index("ix_address_records_review_queue", "needs_review", "review_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("batch_jobs.id", ondelete="CASCADE"), index=True
    )
    sequence: Mapped[int | None] = mapped_column(Integer)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    raw_address: Mapped[str] = mapped_column(Text)
    normalized_address: Mapped[str | None] = mapped_column(Text)
    components: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    corrected_components: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    resolved_reference_ids: Mapped[dict[str, int]] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    review_status: Mapped[str] = mapped_column(
        String(20), default=ReviewStatus.pending.value, index=True
    )
    reviewer_comment: Mapped[str | None] = mapped_column(Text)
    parser_version: Mapped[str] = mapped_column(String(30), default="1.0")
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    error_message: Mapped[str | None] = mapped_column(Text)
    geocoding_status: Mapped[str] = mapped_column(String(20), default="disabled", index=True)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    geocoding_display_name: Mapped[str | None] = mapped_column(Text)
    geocoding_precision: Mapped[str | None] = mapped_column(String(20))
    geocoding_provider: Mapped[str | None] = mapped_column(String(50))
    geocoding_osm_type: Mapped[str | None] = mapped_column(String(20))
    geocoding_osm_id: Mapped[int | None] = mapped_column(Integer)
    geocoded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    batch: Mapped[BatchJob | None] = relationship(back_populates="records")
