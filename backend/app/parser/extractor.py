import re

from app.parser.classifier import classify_segment
from app.parser.patterns import BARE_HOUSE_RE, LABELED_PATTERNS, POSTAL_CODE_RE
from app.parser.tokenizer import tokenize_address
from app.parser.types import ExtractedAddress
from app.reference.aliases import TYPE_ALIASES, detect_street_type


COMPONENT_NAMES = (
    "country",
    "region",
    "district",
    "city",
    "settlement",
    "street",
    "street_type",
    "house",
    "block",
    "building",
    "apartment",
    "entrance",
    "floor",
    "office",
    "postal_code",
)


def _remove_match(text: str, match: re.Match[str]) -> str:
    return f"{text[: match.start()]} {text[match.end() :]}".strip(" ,.")


def _is_country(segment: str) -> bool:
    canonical = segment.casefold().strip(" ,.")
    return canonical in TYPE_ALIASES["country"]


def extract_components(normalized_address: str) -> ExtractedAddress:
    components: dict[str, str | None] = dict.fromkeys(COMPONENT_NAMES)
    unknown_parts: list[str] = []

    for token in tokenize_address(normalized_address):
        segment = token.text

        postal_match = POSTAL_CODE_RE.search(segment)
        if postal_match and components["postal_code"] is None:
            components["postal_code"] = postal_match.group(1)
            segment = _remove_match(segment, postal_match)

        for name, pattern in LABELED_PATTERNS.items():
            match = pattern.search(segment)
            if match and components[name] is None:
                components[name] = match.group(1).strip()
                segment = _remove_match(segment, match)

        segment = re.sub(r"\s+", " ", segment).strip(" ,.")
        if not segment:
            continue

        if _is_country(segment):
            components["country"] = "Казахстан"
            continue

        kind, value = classify_segment(segment)
        if kind is None and components["house"] is None:
            # Kazakh and Russian addresses often omit a house label:
            # "Абай көшесі 25" / "улица Абая 25".
            bare_house_match = BARE_HOUSE_RE.match(segment)
            if bare_house_match:
                possible_kind, possible_value = classify_segment(
                    bare_house_match.group(1).strip()
                )
                if possible_kind == "street":
                    kind = possible_kind
                    value = possible_value
                    components["house"] = bare_house_match.group(2)
        if kind is None:
            unknown_parts.append(segment)
            continue

        if kind == "street" and components["house"] is None:
            bare_house_match = BARE_HOUSE_RE.match(value)
            if bare_house_match:
                value = bare_house_match.group(1).strip()
                components["house"] = bare_house_match.group(2)

        if kind == "street" and components["street_type"] is None:
            components["street_type"] = detect_street_type(segment)

        if value and components[kind] is None:
            components[kind] = value

    # A bare number immediately after a recognized street is usually the house.
    if components["street"] and components["house"] is None:
        for part in list(unknown_parts):
            if re.fullmatch(r"№?[0-9]+[a-zа-я]?(?:[/\-][0-9a-zа-я]+)?", part):
                components["house"] = part.removeprefix("№")
                unknown_parts.remove(part)
                break

    warnings = []
    if unknown_parts:
        warnings.append("Не распознаны части адреса: " + "; ".join(unknown_parts))
    return ExtractedAddress(
        components=components,
        unknown_parts=unknown_parts,
        warnings=warnings,
    )
