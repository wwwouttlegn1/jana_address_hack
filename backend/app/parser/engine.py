from __future__ import annotations

from app.config import get_settings
from app.parser.confidence import calculate_confidence
from app.parser.extractor import extract_components
from app.parser.normalizer import normalize_address
from app.parser.resolver import resolve_components
from app.parser.types import ParserOutput
from app.reference.repository import ReferenceRepository


class AddressParser:
    version = "1.0"

    def __init__(self, repository: ReferenceRepository | None = None) -> None:
        self.repository = repository
        self.settings = get_settings()

    async def parse(self, raw_address: str) -> ParserOutput:
        normalized = normalize_address(raw_address)
        extracted = extract_components(normalized)
        resolved = await resolve_components(extracted.components, self.repository)
        warnings = [*extracted.warnings, *resolved.warnings]
        confidence = calculate_confidence(resolved.components, resolved.scores)

        if not (resolved.components.get("city") or resolved.components.get("settlement")):
            warnings.append("Не определен населенный пункт")
        if not resolved.components.get("street"):
            warnings.append("Не определена улица")
        if not resolved.components.get("house"):
            warnings.append("Не определен номер дома")

        needs_review = confidence < self.settings.review_confidence_threshold or bool(
            extracted.unknown_parts
        )
        return ParserOutput(
            raw_address=raw_address,
            normalized_address=normalized,
            components=resolved.components,
            resolved_reference_ids=resolved.reference_ids,
            confidence=confidence,
            needs_review=needs_review,
            warnings=list(dict.fromkeys(warnings)),
        )
