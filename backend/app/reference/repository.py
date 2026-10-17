from __future__ import annotations

from sqlalchemy import Select, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.parser.normalizer import canonicalize_name
from app.reference.matcher import MatchResult, find_best_match
from app.reference.models import AddressReference, ReferenceType


class ReferenceRepository:
    """Database access and fuzzy lookup for the address reference catalog."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.match_threshold = get_settings().reference_match_threshold

    def _base_query(
        self, kind: ReferenceType | str, parent_id: int | None = None
    ) -> Select[tuple[AddressReference]]:
        query = select(AddressReference).where(
            AddressReference.kind == str(kind.value if isinstance(kind, ReferenceType) else kind),
            AddressReference.enabled.is_(True),
        )
        if parent_id is not None:
            query = query.where(AddressReference.parent_id == parent_id)
        return query

    async def get(self, reference_id: int) -> AddressReference | None:
        return await self.session.get(AddressReference, reference_id)

    async def get_by_code(self, code: str) -> AddressReference | None:
        return await self.session.scalar(
            select(AddressReference).where(AddressReference.code == code).limit(1)
        )

    async def has_entries(self, kind: ReferenceType | str) -> bool:
        kind_value = str(kind.value if isinstance(kind, ReferenceType) else kind)
        return bool(
            await self.session.scalar(
                select(exists().where(
                    AddressReference.kind == kind_value,
                    AddressReference.enabled.is_(True),
                ))
            )
        )

    async def list_by_type(
        self,
        kind: ReferenceType | str,
        *,
        parent_id: int | None = None,
        limit: int = 500,
    ) -> list[AddressReference]:
        query = self._base_query(kind, parent_id).order_by(AddressReference.name).limit(limit)
        return list((await self.session.scalars(query)).all())

    async def resolve(
        self,
        kind: ReferenceType | str,
        name: str,
        *,
        parent_id: int | None = None,
    ) -> MatchResult[AddressReference] | None:
        normalized = canonicalize_name(name)
        if not normalized:
            return None

        query = self._base_query(kind, parent_id).where(
            AddressReference.normalized_name == normalized
        )
        exact = await self.session.scalar(query.limit(1))
        if exact is not None:
            return MatchResult(item=exact, score=100.0)

        words = [word for word in normalized.split() if len(word) >= 3]
        candidate_query = self._base_query(kind, parent_id)
        if words:
            candidate_query = candidate_query.where(
                AddressReference.normalized_name.contains(max(words, key=len))
            )
        candidates = list((await self.session.scalars(candidate_query.limit(500))).all())
        match = find_best_match(normalized, candidates)
        if match is None or match.score < self.match_threshold:
            return None
        return match

    async def upsert(
        self,
        *,
        kind: ReferenceType | str,
        name: str,
        code: str | None = None,
        parent_id: int | None = None,
        attributes: dict[str, object] | None = None,
    ) -> AddressReference:
        normalized = canonicalize_name(name)
        kind_value = str(kind.value if isinstance(kind, ReferenceType) else kind)
        query = self._base_query(kind_value, parent_id).where(
            AddressReference.normalized_name == normalized
        )
        item = await self.session.scalar(query.limit(1))
        if item is None:
            item = AddressReference(
                kind=kind_value,
                name=name.strip(),
                normalized_name=normalized,
                code=code,
                parent_id=parent_id,
                attributes=attributes or {},
            )
            self.session.add(item)
        else:
            item.name = name.strip()
            item.code = code or item.code
            item.attributes = attributes or item.attributes
            item.enabled = True
        await self.session.flush()
        return item
