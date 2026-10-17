from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AddressToken:
    index: int
    text: str
    words: tuple[str, ...]


@dataclass(slots=True)
class ExtractedAddress:
    components: dict[str, str | None]
    unknown_parts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParserOutput:
    raw_address: str
    normalized_address: str
    components: dict[str, Any]
    resolved_reference_ids: dict[str, int]
    confidence: float
    needs_review: bool
    warnings: list[str]
