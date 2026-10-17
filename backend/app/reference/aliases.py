TYPE_ALIASES: dict[str, tuple[str, ...]] = {
    "country": ("казахстан", "қазақстан", "республика казахстан", "qazaqstan"),
    "region": ("область", "обл", "облысы", "обл."),
    "district": ("район", "р-н", "аудан", "ауданы"),
    "city": ("город", "г", "г.", "қала", "қаласы", "қ"),
    "settlement": ("село", "с", "с.", "ауыл", "поселок", "п", "п."),
    "street": (
        "улица",
        "ул",
        "ул.",
        "көшесі",
        "көше",
        "проспект",
        "пр-т",
        "проспекті",
        "микрорайон",
        "мкр",
        "мкр.",
        "шоссе",
        "переулок",
        "пер",
        "пер.",
    ),
}

STREET_TYPE_ALIASES: dict[str, tuple[str, ...]] = {
    "проспект": ("проспект", "пр-т", "проспекті"),
    "улица": ("улица", "ул", "ул."),
    "көше": ("көшесі", "көше"),
    "микрорайон": ("микрорайон", "мкр", "мкр."),
    "переулок": ("переулок", "пер", "пер."),
    "шоссе": ("шоссе",),
}


def strip_type_alias(value: str, kind: str) -> str:
    result = value.strip(" ,.")
    aliases = sorted(TYPE_ALIASES.get(kind, ()), key=len, reverse=True)
    lowered = result.casefold()
    for alias in aliases:
        prefix = f"{alias.casefold()} "
        suffix = f" {alias.casefold()}"
        if lowered.startswith(prefix):
            return result[len(alias) :].strip(" ,.")
        if lowered.endswith(suffix):
            return result[: -len(alias)].strip(" ,.")
    return result


def detect_street_type(value: str) -> str | None:
    lowered = value.casefold().strip(" ,.")
    for canonical, aliases in STREET_TYPE_ALIASES.items():
        for alias in aliases:
            for alias_lower in {alias.casefold(), alias.casefold().strip(".")}:
                if (
                    lowered.startswith(f"{alias_lower} ")
                    or lowered.endswith(f" {alias_lower}")
                    or f" {alias_lower} " in lowered
                ):
                    return canonical
    return None
