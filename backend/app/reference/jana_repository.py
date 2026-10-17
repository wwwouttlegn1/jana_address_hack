from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.parser.challenge import recalculate_confidence
from app.parser.normalizer import canonicalize_name
from app.schemas.challenge import AddressResult


logger = logging.getLogger(__name__)

STREET_TYPES = {
    "street": "улица",
    "avenue": "проспект",
    "lane": "переулок",
    "boulevard": "бульвар",
    "highway": "шоссе",
    "square": "площадь",
}


@dataclass(frozen=True, slots=True)
class StreetCandidate:
    name: str
    street_type: str | None
    province: str | None
    district: str | None
    city: str | None
    nearest_settlement: str | None
    nearest_settlement_km: float | None
    segment_count: int


@dataclass(frozen=True, slots=True)
class PlaceCandidate:
    name: str
    province: str | None
    district: str | None


@dataclass(frozen=True, slots=True)
class AreaCandidate:
    name: str
    province: str | None
    district: str | None
    city: str | None
    nearest_settlement: str | None
    nearest_settlement_km: float | None


class JanaReferenceRepository:
    """Read-only resolver for the imported ``jana_reference`` OSM catalog."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._available: bool | None = None
        self._street_cache: dict[tuple[str, str], list[StreetCandidate]] = {}
        self._place_cache: dict[str, list[PlaceCandidate]] = {}
        self._area_cache: dict[tuple[str, str], list[AreaCandidate]] = {}

    async def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        bind = self.session.get_bind()
        if bind.dialect.name != "postgresql":
            self._available = False
            return False
        relation = await self.session.scalar(
            text("SELECT to_regclass('jana_reference.streets')")
        )
        self._available = relation is not None
        return self._available

    async def enrich(self, result: AddressResult) -> AddressResult:
        """Fill verified hierarchy fields while preserving the public API shape."""

        if not await self.is_available():
            return result
        try:
            await self._resolve_explicit_city(result)
            await self._resolve_living_area(result)
            await self._resolve_street(result)
            result.confidence = recalculate_confidence(result)
        except SQLAlchemyError:
            logger.exception("Не удалось обратиться к схеме jana_reference")
            await self.session.rollback()
        return result

    async def _resolve_explicit_city(self, result: AddressResult) -> None:
        if not result.city:
            return
        normalized = canonicalize_name(result.city)
        if not normalized:
            return
        candidates = self._place_cache.get(normalized)
        if candidates is None:
            rows = (
                await self.session.execute(
                    text(
                        """
                        WITH matched AS (
                            SELECT 'settlements' AS source_table, s.osm_type, s.osm_id
                            FROM jana_reference.settlements AS s
                            WHERE lower(s.name) = lower(:name)
                               OR lower(nullif(s.name_ru, '')) = lower(:name)
                               OR lower(nullif(s.name_kk, '')) = lower(:name)
                            UNION
                            SELECT a.object_kind, a.osm_type, a.osm_id
                            FROM jana_reference.aliases AS a
                            WHERE a.object_kind IN ('places', 'settlements')
                              AND a.normalized_alias_core = :normalized
                        ), places AS (
                            SELECT
                                coalesce(nullif(s.name_ru, ''), s.name) AS name,
                                s.province,
                                s.district
                            FROM matched AS m
                            JOIN jana_reference.settlements AS s
                              ON m.source_table = 'settlements'
                             AND s.osm_type = m.osm_type
                             AND s.osm_id = m.osm_id
                            UNION ALL
                            SELECT
                                coalesce(nullif(p.name_ru, ''), p.name) AS name,
                                p.province,
                                p.district
                            FROM matched AS m
                            JOIN jana_reference.places AS p
                              ON m.source_table = 'places'
                             AND p.osm_type = m.osm_type
                             AND p.osm_id = m.osm_id
                        )
                        SELECT name, province, district
                        FROM places
                        GROUP BY name, province, district
                        LIMIT 30
                        """
                    ),
                    {"name": result.city, "normalized": normalized},
                )
            ).mappings()
            candidates = [
                PlaceCandidate(
                    name=row["name"],
                    province=row["province"],
                    district=row["district"],
                )
                for row in rows
            ]
            self._place_cache[normalized] = candidates

        if not candidates:
            return
        if result.province:
            scoped = [item for item in candidates if item.province == result.province]
            if scoped:
                candidates = scoped
        contexts = {(item.name, item.province) for item in candidates}
        if len(contexts) != 1:
            return
        candidate = candidates[0]
        result.city = candidate.name
        result.province = result.province or candidate.province
        # A city reference cannot identify an intracity district by itself.
        # District is filled only from an unambiguous street/area match.

    async def _resolve_living_area(self, result: AddressResult) -> None:
        source_name = result.living_area
        if source_name is None and result.street_type in {"микрорайон", "квартал"}:
            source_name = result.street_name
        if not source_name:
            return

        normalized = canonicalize_name(source_name)
        if not normalized:
            return
        city = result.city or ""
        cache_key = (normalized, city.casefold())
        candidates = self._area_cache.get(cache_key)
        if candidates is None:
            rows = (
                await self.session.execute(
                    text(
                        """
                        WITH matched AS (
                            SELECT a.osm_type, a.osm_id
                            FROM jana_reference.aliases AS a
                            WHERE a.object_kind = 'living_areas'
                              AND a.normalized_alias_core = :normalized
                            UNION
                            SELECT l.osm_type, l.osm_id
                            FROM jana_reference.living_areas AS l
                            WHERE lower(l.name) = lower(:name)
                               OR lower(nullif(l.name_ru, '')) = lower(:name)
                               OR lower(nullif(l.name_kk, '')) = lower(:name)
                        )
                        SELECT
                            coalesce(nullif(l.name_ru, ''), l.name) AS name,
                            l.province,
                            l.district,
                            nullif(l.city, '') AS city,
                            nullif(l.nearest_settlement, '') AS nearest_settlement,
                            min(l.nearest_settlement_km) AS nearest_settlement_km
                        FROM matched AS m
                        JOIN jana_reference.living_areas AS l
                          ON l.osm_type = m.osm_type AND l.osm_id = m.osm_id
                        WHERE :city = ''
                           OR lower(nullif(l.city, '')) = lower(:city)
                           OR lower(nullif(l.nearest_settlement, '')) = lower(:city)
                        GROUP BY
                            coalesce(nullif(l.name_ru, ''), l.name),
                            l.province,
                            l.district,
                            nullif(l.city, ''),
                            nullif(l.nearest_settlement, '')
                        LIMIT 30
                        """
                    ),
                    {"normalized": normalized, "name": source_name, "city": city},
                )
            ).mappings()
            candidates = [
                AreaCandidate(
                    name=row["name"],
                    province=row["province"],
                    district=row["district"],
                    city=row["city"],
                    nearest_settlement=row["nearest_settlement"],
                    nearest_settlement_km=row["nearest_settlement_km"],
                )
                for row in rows
            ]
            self._area_cache[cache_key] = candidates

        if not candidates:
            return
        contexts = {
            (item.province, item.city or item.nearest_settlement)
            for item in candidates
        }
        if not result.city and len(contexts) != 1:
            return

        result.living_area = candidates[0].name
        provinces = {item.province for item in candidates if item.province}
        if result.province is None and len(provinces) == 1:
            result.province = provinces.pop()
        cities = {item.city for item in candidates if item.city}
        if result.city is None and len(cities) == 1:
            result.city = cities.pop()
        districts = {item.district for item in candidates if item.district}
        if result.district is None and len(districts) == 1:
            result.district = districts.pop()

    async def _resolve_street(self, result: AddressResult) -> None:
        if not result.street_name:
            return
        normalized = canonicalize_name(result.street_name)
        if not normalized:
            return
        city = result.city or ""
        cache_key = (normalized, city.casefold())
        candidates = self._street_cache.get(cache_key)
        if candidates is None:
            rows = (
                await self.session.execute(
                    text(
                        """
                        WITH matched AS (
                            SELECT s.osm_type, s.osm_id
                            FROM jana_reference.streets AS s
                            WHERE s.normalized_core = :normalized
                            UNION
                            SELECT a.osm_type, a.osm_id
                            FROM jana_reference.aliases AS a
                            WHERE a.object_kind = 'streets'
                              AND a.normalized_alias_core = :normalized
                        ), matched_cores AS (
                            SELECT DISTINCT s.normalized_core
                            FROM matched AS m
                            JOIN jana_reference.streets AS s
                              ON s.osm_type = m.osm_type AND s.osm_id = m.osm_id
                        ), expanded AS (
                            SELECT s.*
                            FROM jana_reference.streets AS s
                            JOIN matched_cores AS c
                              ON c.normalized_core = s.normalized_core
                        )
                        SELECT
                            coalesce(nullif(s.street_name_core, ''), s.name) AS name,
                            s.street_type,
                            s.province,
                            s.district,
                            nullif(s.city, '') AS city,
                            nullif(s.nearest_settlement, '') AS nearest_settlement,
                            min(s.nearest_settlement_km) AS nearest_settlement_km,
                            count(*)::int AS segment_count
                        FROM expanded AS s
                        WHERE :city = ''
                           OR lower(nullif(s.city, '')) = lower(:city)
                           OR lower(nullif(s.nearest_settlement, '')) = lower(:city)
                        GROUP BY
                            coalesce(nullif(s.street_name_core, ''), s.name),
                            s.street_type,
                            s.province,
                            s.district,
                            nullif(s.city, ''),
                            nullif(s.nearest_settlement, '')
                        ORDER BY count(*) DESC
                        LIMIT 50
                        """
                    ),
                    {"normalized": normalized, "city": city},
                )
            ).mappings()
            candidates = [
                StreetCandidate(
                    name=row["name"],
                    street_type=row["street_type"],
                    province=row["province"],
                    district=row["district"],
                    city=row["city"],
                    nearest_settlement=row["nearest_settlement"],
                    nearest_settlement_km=row["nearest_settlement_km"],
                    segment_count=row["segment_count"],
                )
                for row in rows
            ]
            self._street_cache[cache_key] = candidates

        if not candidates:
            return

        contexts = {
            (item.province, item.city or item.nearest_settlement)
            for item in candidates
        }
        if not result.city and len(contexts) != 1:
            # A street name occurring in several cities is not enough to infer one.
            return

        candidate = max(candidates, key=lambda item: item.segment_count)
        # Keep the spelling entered by the client (for example, Russian
        # ``Жандосова`` versus the Kazakh catalog core ``Жандосов``).
        result.street_type = result.street_type or STREET_TYPES.get(candidate.street_type or "")
        result.province = result.province or candidate.province

        cities = {item.city for item in candidates if item.city}
        if result.city is None and len(cities) == 1:
            result.city = cities.pop()
        elif result.city is None:
            nearby = {
                item.nearest_settlement
                for item in candidates
                if item.nearest_settlement
                and item.nearest_settlement_km is not None
                and item.nearest_settlement_km <= 5.0
            }
            if len(nearby) == 1:
                result.city = nearby.pop()

        districts = {item.district for item in candidates if item.district}
        if result.district is None and len(districts) == 1:
            result.district = districts.pop()
