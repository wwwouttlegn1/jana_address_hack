from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.parser.engine import AddressParser
from app.reference.repository import ReferenceRepository
from app.schemas.address import BatchAddressItem
from app.services.geocoding_service import GeocodingService
from app.storage.database import async_session_factory
from app.storage.models import AddressRecord, BatchJob, BatchStatus


logger = logging.getLogger(__name__)


class BatchNotFoundError(LookupError):
    pass


class BatchStateError(RuntimeError):
    pass


class BatchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        items: list[BatchAddressItem],
        *,
        source_type: str,
        source_name: str | None = None,
    ) -> BatchJob:
        settings = get_settings()
        if len(items) > settings.max_batch_size:
            raise ValueError(f"Максимальный размер пакета: {settings.max_batch_size}")

        batch = BatchJob(
            status=BatchStatus.queued.value,
            source_type=source_type,
            source_name=source_name,
            total_count=len(items),
        )
        self.session.add(batch)
        await self.session.flush()
        self.session.add_all(
            [
                AddressRecord(
                    batch_id=batch.id,
                    sequence=index,
                    external_id=item.external_id,
                    raw_address=item.address,
                )
                for index, item in enumerate(items)
            ]
        )
        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def get(self, batch_id: uuid.UUID) -> BatchJob:
        batch = await self.session.get(BatchJob, batch_id)
        if batch is None:
            raise BatchNotFoundError("Пакет не найден")
        return batch

    async def list(
        self, *, page: int, page_size: int
    ) -> tuple[list[BatchJob], int]:
        total = await self.session.scalar(select(func.count(BatchJob.id))) or 0
        query = (
            select(BatchJob)
            .order_by(BatchJob.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list((await self.session.scalars(query)).all()), total

    async def get_records(
        self, batch_id: uuid.UUID, *, page: int, page_size: int
    ) -> tuple[list[AddressRecord], int]:
        await self.get(batch_id)
        filters = AddressRecord.batch_id == batch_id
        total = await self.session.scalar(select(func.count()).where(filters)) or 0
        query = (
            select(AddressRecord)
            .where(filters)
            .order_by(AddressRecord.sequence)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list((await self.session.scalars(query)).all()), total


async def process_batch_job(batch_id: uuid.UUID) -> None:
    """Process a persisted job. Safe to call again after a partial failure."""

    settings = get_settings()
    async with async_session_factory() as session:
        try:
            batch = await session.get(BatchJob, batch_id)
            if batch is None:
                logger.error("Batch %s does not exist", batch_id)
                return
            if batch.status == BatchStatus.completed.value:
                return

            batch.status = BatchStatus.processing.value
            batch.started_at = batch.started_at or datetime.now(timezone.utc)
            batch.error_message = None
            await session.commit()

            records = list(
                (
                    await session.scalars(
                        select(AddressRecord)
                        .where(AddressRecord.batch_id == batch_id)
                        .order_by(AddressRecord.sequence)
                    )
                ).all()
            )
            parser = AddressParser(ReferenceRepository(session))
            geocoder = GeocodingService(session)

            for position, record in enumerate(records, start=1):
                if record.normalized_address is not None or record.error_message is not None:
                    continue
                try:
                    output = await parser.parse(record.raw_address)
                    geocoding = await geocoder.geocode(
                        output.normalized_address, output.components
                    )
                    record.normalized_address = output.normalized_address
                    record.components = output.components
                    record.resolved_reference_ids = output.resolved_reference_ids
                    record.confidence = output.confidence
                    record.needs_review = output.needs_review
                    record.warnings = list(
                        dict.fromkeys(
                            [
                                *output.warnings,
                                *([geocoding.warning] if geocoding.warning else []),
                            ]
                        )
                    )
                    record.parser_version = parser.version
                    record.geocoding_status = geocoding.status
                    if geocoding.location is not None:
                        record.latitude = geocoding.location.latitude
                        record.longitude = geocoding.location.longitude
                        record.geocoding_display_name = geocoding.location.display_name
                        record.geocoding_precision = geocoding.location.precision
                        record.geocoding_provider = geocoding.location.provider
                        record.geocoding_osm_type = geocoding.location.osm_type
                        record.geocoding_osm_id = geocoding.location.osm_id
                        record.geocoded_at = datetime.now(timezone.utc)
                except Exception as exc:  # row-level isolation is intentional
                    logger.exception("Failed to parse row %s in batch %s", record.id, batch_id)
                    record.error_message = str(exc)[:2_000]
                    record.needs_review = True

                if position % settings.batch_checkpoint_size == 0:
                    _update_batch_counters(batch, records)
                    await session.commit()

            _update_batch_counters(batch, records)
            batch.status = (
                BatchStatus.failed.value
                if batch.success_count == 0 and batch.error_count > 0
                else BatchStatus.completed.value
            )
            batch.completed_at = datetime.now(timezone.utc)
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.exception("Batch %s failed", batch_id)
            batch = await session.get(BatchJob, batch_id)
            if batch is not None:
                batch.status = BatchStatus.failed.value
                batch.error_message = str(exc)[:2_000]
                batch.completed_at = datetime.now(timezone.utc)
                await session.commit()


def _update_batch_counters(batch: BatchJob, records: list[AddressRecord]) -> None:
    processed = [r for r in records if r.normalized_address is not None or r.error_message]
    batch.processed_count = len(processed)
    batch.error_count = sum(1 for r in processed if r.error_message)
    batch.success_count = sum(1 for r in processed if not r.error_message)
    batch.review_count = sum(1 for r in processed if r.needs_review and not r.error_message)
