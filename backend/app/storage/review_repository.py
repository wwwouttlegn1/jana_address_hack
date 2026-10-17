from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.review import ReviewUpdateRequest
from app.storage.models import AddressRecord, ReviewStatus


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, record_id: uuid.UUID) -> AddressRecord | None:
        return await self.session.get(AddressRecord, record_id)

    async def list(
        self,
        *,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[AddressRecord], int]:
        query = select(AddressRecord)
        count_query = select(func.count()).select_from(AddressRecord)
        if status:
            query = query.where(AddressRecord.review_status == status)
            count_query = count_query.where(AddressRecord.review_status == status)
        else:
            query = query.where(AddressRecord.needs_review.is_(True))
            count_query = count_query.where(AddressRecord.needs_review.is_(True))

        total = await self.session.scalar(count_query) or 0
        records = list(
            (
                await self.session.scalars(
                    query.order_by(AddressRecord.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ).all()
        )
        return records, total

    async def update(
        self, record: AddressRecord, request: ReviewUpdateRequest
    ) -> AddressRecord:
        record.review_status = request.status
        record.reviewer_comment = request.comment
        record.reviewed_at = datetime.now(timezone.utc)
        record.needs_review = False
        if request.status == ReviewStatus.corrected.value and request.components is not None:
            record.corrected_components = request.components.model_dump()
            record.confidence = 1.0
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def stats(self) -> dict[str, int]:
        rows = (
            await self.session.execute(
                select(AddressRecord.review_status, func.count(AddressRecord.id)).group_by(
                    AddressRecord.review_status
                )
            )
        ).all()
        values = {status: count for status, count in rows}
        return {status.value: values.get(status.value, 0) for status in ReviewStatus}
