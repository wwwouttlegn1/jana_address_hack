from __future__ import annotations

from dataclasses import dataclass, field

from app.reference.models import ReferenceType
from app.reference.repository import ReferenceRepository


FIELD_REFERENCE_TYPES = {
    "country": ReferenceType.country,
    "region": ReferenceType.region,
    "district": ReferenceType.district,
    "city": ReferenceType.city,
    "settlement": ReferenceType.settlement,
    "street": ReferenceType.street,
}


@dataclass(slots=True)
class ResolutionResult:
    components: dict[str, str | None]
    reference_ids: dict[str, int] = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


async def resolve_components(
    components: dict[str, str | None],
    repository: ReferenceRepository | None,
) -> ResolutionResult:
    result = ResolutionResult(components=components.copy())
    if repository is None:
        return result

    parent_id: int | None = None
    for field_name in ("country", "region", "district", "city", "settlement", "street"):
        value = result.components.get(field_name)
        if not value:
            continue
        # Street catalogs are commonly scoped to a city/settlement. Other levels may be
        # global in imported datasets, so a strict parent filter is not forced there.
        match_parent = parent_id if field_name == "street" else None
        match = await repository.resolve(
            FIELD_REFERENCE_TYPES[field_name], value, parent_id=match_parent
        )
        if match is None and match_parent is not None:
            match = await repository.resolve(FIELD_REFERENCE_TYPES[field_name], value)
        if match is None:
            if await repository.has_entries(FIELD_REFERENCE_TYPES[field_name]):
                result.warnings.append(
                    f"Нет совпадения в справочнике для поля {field_name}: {value}"
                )
            continue
        result.components[field_name] = match.item.name
        result.reference_ids[field_name] = match.item.id
        result.scores[field_name] = match.score
        if field_name in {"country", "region", "district", "city", "settlement"}:
            parent_id = match.item.id
    return result
