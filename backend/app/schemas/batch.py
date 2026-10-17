from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.address import ParseAddressResult


class BatchCreateRequest(BaseModel):
    items: list[str] = Field(
        min_length=1,
        description="Адреса в свободной форме",
        examples=[["г. Алматы, ул. Абая, д. 10", "г. Астана, ул. Сыганак, д. 5"]],
    )
    source_name: str | None = Field(
        default=None,
        max_length=255,
        description="Понятное название списка",
        examples=["Заказы за 16 октября"],
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "source_name": "Демо хакатона",
                "items": [
                    "г. Алматы, ул. Абая, д. 10",
                    "г. Астана, ул. Сыганак, д. 5",
                ],
            }
        },
    )


class BatchJobResponse(BaseModel):
    id: uuid.UUID
    status: str
    source_type: str
    source_name: str | None
    total_count: int
    processed_count: int
    success_count: int
    review_count: int
    error_count: int
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class BatchResultsResponse(BaseModel):
    batch: BatchJobResponse
    items: list[ParseAddressResult]
    total: int
    page: int
    page_size: int


class BatchListResponse(BaseModel):
    items: list[BatchJobResponse]
    total: int
    page: int
    page_size: int
