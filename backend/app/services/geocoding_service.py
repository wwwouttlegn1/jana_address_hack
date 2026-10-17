from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

import httpx
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.parser.normalizer import canonicalize_name
from app.schemas.address import GeoLocation
from app.storage.models import AddressRecord


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GeocodingOutcome:
    status: str
    location: GeoLocation | None = None
    warning: str | None = None


class GeocodingService:
    """Geocode normalized Kazakhstan addresses with caching and rate limiting."""

    provider_name = "OpenStreetMap Nominatim (ranked-v2)"
    _request_lock = asyncio.Lock()
    _last_request_at = 0.0

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    async def geocode(
        self,
        normalized_address: str,
        components: dict[str, object],
    ) -> GeocodingOutcome:
        if not self.settings.geocoding_enabled:
            return GeocodingOutcome(status="disabled")

        cached = await self._get_cached(normalized_address)
        if cached is not None:
            return GeocodingOutcome(status="found", location=cached)

        query = self._build_public_query(components)
        if not query:
            return GeocodingOutcome(
                status="not_found",
                warning="Недостаточно данных для поиска координат",
            )

        try:
            payload = await self._request(query)
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Geocoder request failed for %r: %s", query, exc)
            return GeocodingOutcome(
                status="error",
                warning="Сервис координат временно недоступен; нормализация выполнена",
            )

        if not payload:
            return GeocodingOutcome(
                status="not_found",
                warning="Координаты для нормализованного адреса не найдены",
            )

        item = self._select_best(payload, components)
        try:
            latitude = float(item["lat"])
            longitude = float(item["lon"])
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Geocoder returned invalid coordinates: %s", exc)
            return GeocodingOutcome(status="error", warning="Геокодер вернул некорректные данные")

        return GeocodingOutcome(
            status="found",
            location=GeoLocation(
                latitude=latitude,
                longitude=longitude,
                display_name=str(item.get("display_name") or query),
                precision=self._detect_precision(components, item),
                provider=self.provider_name,
                map_url=(
                    "https://www.openstreetmap.org/"
                    f"?mlat={latitude}&mlon={longitude}#map=18/{latitude}/{longitude}"
                ),
                attribution="© OpenStreetMap contributors, ODbL 1.0",
                osm_type=str(item["osm_type"]) if item.get("osm_type") else None,
                osm_id=int(item["osm_id"]) if item.get("osm_id") is not None else None,
            ),
        )

    async def _get_cached(self, normalized_address: str) -> GeoLocation | None:
        record = await self.session.scalar(
            select(AddressRecord)
            .where(
                AddressRecord.normalized_address == normalized_address,
                AddressRecord.geocoding_status == "found",
                AddressRecord.geocoding_provider == self.provider_name,
                AddressRecord.latitude.is_not(None),
                AddressRecord.longitude.is_not(None),
            )
            .order_by(AddressRecord.created_at.desc())
            .limit(1)
        )
        if record is None or record.latitude is None or record.longitude is None:
            return None
        return GeoLocation(
            latitude=record.latitude,
            longitude=record.longitude,
            display_name=record.geocoding_display_name or normalized_address,
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

    def _build_public_query(self, components: dict[str, object]) -> str:
        # Apartment, entrance, floor and office are deliberately excluded: they do
        # not improve geocoding and should not be sent to an external provider.
        street = components.get("street")
        street_part = " ".join(
            str(part).strip()
            for part in (
                components.get("street_type"),
                street,
                components.get("house"),
            )
            if part
        )
        parts = [
            street_part or None,
            components.get("city") or components.get("settlement"),
            components.get("district"),
            components.get("region"),
            components.get("country") or "Казахстан",
        ]
        meaningful = [str(part).strip() for part in parts if part]
        return ", ".join(meaningful) if len(meaningful) > 1 else ""

    async def _request(self, query: str) -> list[dict[str, object]]:
        async with self._request_lock:
            elapsed = time.monotonic() - self._last_request_at
            delay = self.settings.geocoder_min_interval_seconds - elapsed
            if delay > 0:
                await asyncio.sleep(delay)

            async with httpx.AsyncClient(
                base_url=self.settings.geocoder_base_url.rstrip("/"),
                timeout=self.settings.geocoder_timeout_seconds,
                follow_redirects=True,
                headers={
                    "User-Agent": self.settings.geocoder_user_agent,
                    "Accept-Language": "ru,kk;q=0.9,en;q=0.5",
                },
            ) as client:
                response = await client.get(
                    "/search",
                    params={
                        "q": query,
                        "format": "jsonv2",
                        "addressdetails": 1,
                        "countrycodes": "kz",
                        "limit": 5,
                    },
                )
                self.__class__._last_request_at = time.monotonic()
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, list):
                    raise ValueError("Geocoder response must be a list")
                return payload

    @staticmethod
    def _select_best(
        candidates: list[dict[str, object]], components: dict[str, object]
    ) -> dict[str, object]:
        expected_house = canonicalize_name(str(components.get("house") or ""))
        expected_street = canonicalize_name(str(components.get("street") or ""))
        expected_city = canonicalize_name(
            str(components.get("city") or components.get("settlement") or "")
        )

        def score(candidate: dict[str, object]) -> float:
            address_value = candidate.get("address")
            address = address_value if isinstance(address_value, dict) else {}
            total = float(candidate.get("importance") or 0.0) * 5

            if expected_house:
                provider_house = canonicalize_name(str(address.get("house_number") or ""))
                if provider_house == expected_house:
                    total += 60
                elif provider_house:
                    total -= 30

            if expected_street:
                provider_street = canonicalize_name(
                    str(
                        address.get("road")
                        or address.get("pedestrian")
                        or address.get("residential")
                        or ""
                    )
                )
                if provider_street:
                    total += fuzz.WRatio(expected_street, provider_street) * 0.3

            if expected_city:
                provider_city = canonicalize_name(
                    str(
                        address.get("city")
                        or address.get("town")
                        or address.get("municipality")
                        or ""
                    )
                )
                if provider_city:
                    total += fuzz.WRatio(expected_city, provider_city) * 0.2
            return total

        return max(candidates, key=score)

    @staticmethod
    def _detect_precision(
        components: dict[str, object], provider_result: dict[str, object]
    ) -> str:
        address = provider_result.get("address")
        address_parts = address if isinstance(address, dict) else {}
        result_type = str(provider_result.get("addresstype") or provider_result.get("type") or "")
        if components.get("house") and (
            address_parts.get("house_number") or result_type in {"house", "building"}
        ):
            return "house"
        if components.get("street") and (
            address_parts.get("road")
            or address_parts.get("pedestrian")
            or result_type in {"road", "street"}
        ):
            return "street"
        if components.get("city") or components.get("settlement"):
            return "settlement"
        if components.get("region"):
            return "region"
        return "unknown"
