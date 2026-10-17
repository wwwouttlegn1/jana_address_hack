from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, Protocol, TypeVar

from rapidfuzz import fuzz


class NamedReference(Protocol):
    name: str
    normalized_name: str


T = TypeVar("T", bound=NamedReference)


@dataclass(frozen=True, slots=True)
class MatchResult(Generic[T]):
    item: T
    score: float


def find_best_match(query: str, candidates: Iterable[T]) -> MatchResult[T] | None:
    best: MatchResult[T] | None = None
    for candidate in candidates:
        score = float(fuzz.WRatio(query, candidate.normalized_name))
        if best is None or score > best.score:
            best = MatchResult(item=candidate, score=score)
    return best
