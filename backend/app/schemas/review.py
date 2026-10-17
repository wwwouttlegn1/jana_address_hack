from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.address import AddressComponents


class ReviewItemResponse(BaseModel):
    id: uuid.UUID
    batch_id: uuid.UUID | None
    external_id: str | None
    raw_address: str
    normalized_address: str | None
    components: AddressComponents
    corrected_components: AddressComponents | None
    confidence: float
    needs_review: bool
    review_status: str
    warnings: list[str]
    reviewer_comment: str | None
    created_at: datetime
    reviewed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(BaseModel):
    items: list[ReviewItemResponse]
    total: int
    page: int
    page_size: int


class ReviewUpdateRequest(BaseModel):
    status: Literal["approved", "corrected", "rejected"] = Field(
        description="approved — подтвердить, corrected — исправить, rejected — отклонить"
    )
    components: AddressComponents | None = Field(
        default=None, description="Обязательно только для статуса corrected"
    )
    comment: str | None = Field(
        default=None, max_length=2_000, description="Комментарий оператора"
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def corrected_requires_components(self) -> ReviewUpdateRequest:
        if self.status == "corrected" and self.components is None:
            raise ValueError("components are required when status is corrected")
        return self


class ReviewStatsResponse(BaseModel):
    pending: int
    approved: int
    corrected: int
    rejected: int
