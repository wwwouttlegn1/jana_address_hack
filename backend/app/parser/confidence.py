from collections.abc import Mapping


FIELD_WEIGHTS = {
    "country": 0.03,
    "region": 0.10,
    "district": 0.04,
    "city": 0.22,
    "settlement": 0.18,
    "street": 0.28,
    "house": 0.25,
    "postal_code": 0.04,
    "apartment": 0.02,
    "building": 0.02,
    "block": 0.02,
}


def calculate_confidence(
    components: Mapping[str, object],
    reference_scores: Mapping[str, float] | None = None,
) -> float:
    score = sum(weight for field, weight in FIELD_WEIGHTS.items() if components.get(field))

    # City and settlement represent the same hierarchy level; do not double count them.
    if components.get("city") and components.get("settlement"):
        score -= min(FIELD_WEIGHTS["city"], FIELD_WEIGHTS["settlement"])

    if reference_scores:
        fuzzy_values = [value / 100 for value in reference_scores.values()]
        if fuzzy_values:
            score = score * 0.85 + (sum(fuzzy_values) / len(fuzzy_values)) * 0.15

    return round(max(0.0, min(score, 1.0)), 3)
