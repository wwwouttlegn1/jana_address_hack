from app.reference.aliases import TYPE_ALIASES, strip_type_alias


CLASSIFICATION_ORDER = ("country", "region", "district", "city", "settlement", "street")


def classify_segment(segment: str) -> tuple[str | None, str]:
    lowered = segment.casefold().strip(" ,.")
    for kind in CLASSIFICATION_ORDER:
        for alias in sorted(TYPE_ALIASES[kind], key=len, reverse=True):
            variants = {alias.casefold(), alias.casefold().strip(".")}
            for alias_lower in variants:
                if (
                    lowered == alias_lower
                    or lowered.startswith(f"{alias_lower} ")
                    or lowered.endswith(f" {alias_lower}")
                ):
                    return kind, strip_type_alias(segment, kind)
    return None, segment.strip(" ,.")
