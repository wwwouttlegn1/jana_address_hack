from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.parser.engine import AddressParser
from app.parser.types import ParserOutput
from app.reference.repository import ReferenceRepository
from app.schemas.address import (
    AddressComponents,
    GeoLocation,
    ParseAddressRequest,
    ParseAddressResult,
)
from app.services.geocoding_service import GeocodingOutcome, GeocodingService
from app.storage.models import AddressRecord


def parser_output_to_result(
    output: ParserOutput,
    *,
    record_id: uuid.UUID | None = None,
    external_id: str | None = None,
    geocoding: GeocodingOutcome | None = None,
) -> ParseAddressResult:
    geocoding = geocoding or GeocodingOutcome(status="disabled")
    warnings = list(output.warnings)
    if geocoding.warning:
        warnings.append(geocoding.warning)
    return ParseAddressResult(
        record_id=record_id,
        external_id=external_id,
        raw_address=output.raw_address,
        normalized_address=output.normalized_address,
        components=AddressComponents.model_validate(output.components),
        resolved_reference_ids=output.resolved_reference_ids,
        confidence=output.confidence,
        needs_review=output.needs_review,
        warnings=list(dict.fromkeys(warnings)),
        geocoding_status=geocoding.status,
        location=geocoding.location,
    )


def record_to_result(record: AddressRecord) -> ParseAddressResult:
    components = record.corrected_components or record.components or {}
    location: GeoLocation | None = None
    if record.latitude is not None and record.longitude is not None:
        location = GeoLocation(
            latitude=record.latitude,
            longitude=record.longitude,
            display_name=record.geocoding_display_name or record.normalized_address or "",
            precision=record.geocoding_precision or "unknown",
            provider=record.geocoding_provider or "cache",
            map_url=(
                "https://www.openstreetmap.org/"
                f"?mlat={record.latitude}&mlon={record.longitude}"
                f"#map=18/{record.latitude}/{record.longitude}"
            ),
            attribution="© OpenStreetMap contributors, ODbL 1.0",
            osm_type=record.geocoding_osm_type,
            osm_id=record.geocoding_osm_id,
        )
    return ParseAddressResult(
        record_id=record.id,
        external_id=record.external_id,
        raw_address=record.raw_address,
        normalized_address=record.normalized_address or "",
        components=AddressComponents.model_validate(components),
        resolved_reference_ids=record.resolved_reference_ids or {},
        confidence=record.confidence,
        needs_review=record.needs_review,
        warnings=record.warnings or [],
        geocoding_status=record.geocoding_status,
        location=location,
    )


class AddressService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.parser = AddressParser(ReferenceRepository(session))
        self.geocoder = GeocodingService(session)

    async def parse(
        self,
        request: ParseAddressRequest,
        *,
        batch_id: uuid.UUID | None = None,
        sequence: int | None = None,
    ) -> ParseAddressResult:
        output = await self.parser.parse(request.address)
        geocoding = await self.geocoder.geocode(output.normalized_address, output.components)
        if not request.persist:
            return parser_output_to_result(
                output, external_id=request.external_id, geocoding=geocoding
            )

        record = AddressRecord(
            batch_id=batch_id,
            sequence=sequence,
            external_id=request.external_id,
            raw_address=output.raw_address,
            normalized_address=output.normalized_address,
            components=output.components,
            resolved_reference_ids=output.resolved_reference_ids,
            confidence=output.confidence,
            needs_review=output.needs_review,
            warnings=output.warnings,
            parser_version=self.parser.version,
            geocoding_status=geocoding.status,
        )
        if geocoding.location is not None:
            record.latitude = geocoding.location.latitude
            record.longitude = geocoding.location.longitude
            record.geocoding_display_name = geocoding.location.display_name
            record.geocoding_precision = geocoding.location.precision
            record.geocoding_provider = geocoding.location.provider
            record.geocoding_osm_type = geocoding.location.osm_type
            record.geocoding_osm_id = geocoding.location.osm_id
            record.geocoded_at = datetime.now(timezone.utc)
        if geocoding.warning:
            record.warnings = list(dict.fromkeys([*record.warnings, geocoding.warning]))
        self.session.add(record)
        await self.session.flush()
        return parser_output_to_result(
            output,
            record_id=record.id,
            external_id=request.external_id,
            geocoding=geocoding,
        )

    async def get(self, record_id: uuid.UUID) -> AddressRecord | None:
        return await self.session.get(AddressRecord, record_id)
