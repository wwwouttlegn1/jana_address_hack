from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.parser.challenge import recalculate_confidence
from app.parser.normalizer import normalize_address
from app.schemas.challenge import AddressCorrection, AddressResult
from app.storage.models import AddressRecord, ReviewStatus


COMPONENT_FIELDS = (
    "province",
    "city",
    "district",
    "living_area",
    "street_type",
    "street_name",
    "house",
    "apartment",
    "entrance",
    "floor",
    "landmark",
)


def _result_components(result: AddressResult) -> dict[str, str | None]:
    return {field: getattr(result, field) for field in COMPONENT_FIELDS}


def record_to_challenge_result(record: AddressRecord) -> AddressResult:
    components = record.corrected_components or record.components or {}
    return AddressResult(
        record_id=record.id,
        id=record.external_id or str(record.id),
        raw_address=record.raw_address,
        province=components.get("province") or components.get("region"),
        city=components.get("city"),
        district=components.get("district"),
        living_area=components.get("living_area"),
        street_type=components.get("street_type"),
        street_name=components.get("street_name") or components.get("street"),
        house=components.get("house"),
        apartment=components.get("apartment"),
        entrance=components.get("entrance"),
        floor=components.get("floor"),
        landmark=components.get("landmark"),
        confidence=record.confidence,
        needs_review=record.needs_review,
    )


class ChallengeRecordService:
    """Persistence for the flat challenge API consumed by the frontend."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.review_threshold = get_settings().review_confidence_threshold

    async def save(self, result: AddressResult, *, sequence: int | None = None) -> AddressResult:
        needs_review = result.confidence < self.review_threshold
        record = AddressRecord(
            sequence=sequence,
            external_id=result.id,
            raw_address=result.raw_address,
            normalized_address=normalize_address(result.raw_address),
            components=_result_components(result),
            resolved_reference_ids={},
            confidence=result.confidence,
            needs_review=needs_review,
            review_status=(
                ReviewStatus.pending.value if needs_review else ReviewStatus.approved.value
            ),
            parser_version="challenge-1.0",
            warnings=[],
            geocoding_status="disabled",
        )
        self.session.add(record)
        await self.session.flush()
        result.record_id = record.id
        result.needs_review = needs_review
        return result

    async def list_recent(self, *, limit: int) -> list[AddressResult]:
        records = list(
            (
                await self.session.scalars(
                    select(AddressRecord)
                    .order_by(AddressRecord.created_at.desc())
                    .limit(limit)
                )
            ).all()
        )
        return [record_to_challenge_result(record) for record in records]

    async def correct(
        self, record_id: uuid.UUID, correction: AddressCorrection
    ) -> AddressResult | None:
        record = await self.session.get(AddressRecord, record_id)
        if record is None:
            return None

        components = dict(record.corrected_components or record.components or {})
        components.update(correction.model_dump(exclude_unset=True))
        updated = record_to_challenge_result(record).model_copy(update=components)
        updated.confidence = recalculate_confidence(updated)
        updated.needs_review = False

        record.corrected_components = _result_components(updated)
        record.confidence = updated.confidence
        record.needs_review = False
        record.review_status = ReviewStatus.corrected.value
        await self.session.flush()
        return record_to_challenge_result(record)
