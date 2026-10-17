from __future__ import annotations

import logging
import re
import unicodedata

from app.schemas.challenge import AddressInput, AddressResult


INVISIBLE_CHARS_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
HOUSE_VALUE = r"\d+[A-Za-zА-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІі]?(?:/\d+[A-Za-zА-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІі]?)?"
NUMBER_VALUE = r"\d+"

logger = logging.getLogger(__name__)

TYPE_PATTERN = (
    r"улица|ул\.?|проспект|пр(?:-?т)?\.?|микрорайон|мкр\.?|"
    r"переулок|пер\.?|квартал|көше|көшесі|даңғыл|даңғылы|"
    r"шағын\s+аудан|ықшам\s+аудан"
)
PREFIXED_STREET_RE = re.compile(
    rf"^(?P<type>{TYPE_PATTERN})\s*[:.\-]?\s*(?P<name>.+)$", re.IGNORECASE
)
SUFFIXED_STREET_RE = re.compile(
    rf"^(?P<name>.+?)\s+(?P<type>{TYPE_PATTERN})$", re.IGNORECASE
)
SUFFIXED_STREET_WITH_HOUSE_RE = re.compile(
    rf"^(?P<name>.+?)\s+(?P<type>{TYPE_PATTERN})\s+(?P<house>{HOUSE_VALUE})$",
    re.IGNORECASE,
)
LIVING_AREA_RE = re.compile(
    r"^(?:жк|жилой\s+комплекс|жилой\s+массив|ж/м|массив|"
    r"тұрғын\s+үй\s+кешені|тұрғын\s+алап)\s*[:.\-]?\s*(?P<name>.+)$",
    re.IGNORECASE,
)
LANDMARK_RE = re.compile(
    r"\b(?:магазин|дүкен|qazpost|ориентир|кафе|аптека|школа|тц|бц)\b"
    r"(?:\s*[:.\-]?\s*[^,;]+)?",
    re.IGNORECASE,
)
ONLY_HOUSE_RE = re.compile(rf"^{HOUSE_VALUE}$", re.IGNORECASE)
TRAILING_HOUSE_RE = re.compile(
    rf"^(?P<name>.*?\S)\s+(?P<house>{HOUSE_VALUE})$", re.IGNORECASE
)

REPUBLICAN_CITIES = {"алматы": "Алматы", "астана": "Астана", "шымкент": "Шымкент"}
CITY_ALIASES = {
    **REPUBLICAN_CITIES,
    "ақтөбе": "Актобе",
    "актобе": "Актобе",
    "атырау": "Атырау",
    "ақтау": "Актау",
    "актау": "Актау",
    "қарағанды": "Караганда",
    "караганда": "Караганда",
    "қостанай": "Костанай",
    "костанай": "Костанай",
    "қызылорда": "Кызылорда",
    "кызылорда": "Кызылорда",
    "павлодар": "Павлодар",
    "петропавловск": "Петропавловск",
    "семей": "Семей",
    "тараз": "Тараз",
    "талдықорған": "Талдыкорган",
    "талдыкорган": "Талдыкорган",
    "түркістан": "Туркестан",
    "туркестан": "Туркестан",
    "орал": "Уральск",
    "уральск": "Уральск",
    "өскемен": "Усть-Каменогорск",
    "усть-каменогорск": "Усть-Каменогорск",
}
PROVINCE_ALIASES = {
    "ақтөбе": "Актюбинская область",
    "алматы": "Алматинская область",
    "атырау": "Атырауская область",
    "қарағанды": "Карагандинская область",
    "қостанай": "Костанайская область",
    "қызылорда": "Кызылординская область",
    "павлодар": "Павлодарская область",
    "түркістан": "Туркестанская область",
}


def _clean_source(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = INVISIBLE_CHARS_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _prepare(value: str) -> str:
    """Add missing separators only around structural labels."""

    text = _clean_source(value)
    labels = (
        r"квартал|дом|квартира|подъезд|подьезд|этаж|floor|flat|kv|"
        r"микрорайон|мкр"
    )
    text = re.sub(rf"(?i)(\d)(?=({labels})\b)", r"\1 ", text)
    text = re.sub(rf"(?i)\b({labels})(?=\d)", r"\1 ", text)
    text = re.sub(
        r"(?<=[A-Za-zА-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІі])(?=\d)", " ", text
    )
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _strip_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" \t\r\n.,;:-")


def _canonical_city(value: str) -> str:
    cleaned = _strip_value(value)
    return CITY_ALIASES.get(cleaned.casefold(), cleaned)


def _canonical_type(value: str) -> str:
    token = value.casefold().rstrip(".")
    if token.startswith("ул") or token.startswith("көше"):
        return "улица"
    if token.startswith("пр") or token.startswith("даңғ"):
        return "проспект"
    if (
        token.startswith("мкр")
        or token.startswith("микро")
        or token.startswith("шағын")
        or token.startswith("ықшам")
    ):
        return "микрорайон"
    if token.startswith("пер"):
        return "переулок"
    return "квартал"


def _remove_span(text: str, span: tuple[int, int]) -> str:
    start, end = span
    return f"{text[:start]}{' ' * (end - start)}{text[end:]}"


def _extract_detail(
    text: str, labels: str, value_pattern: str
) -> tuple[str | None, str]:
    patterns = (
        re.compile(
            rf"\b(?:{labels})\s*\.?\s*№?\s*(?P<value>{value_pattern})\b",
            re.IGNORECASE,
        ),
        re.compile(
            rf"(?<!\w)(?P<value>{value_pattern})\s*(?:{labels})\b",
            re.IGNORECASE,
        ),
    )
    direct = patterns[0].search(text)
    reverse = patterns[1].search(text)
    if direct or reverse:
        match = direct or reverse
        if direct and reverse:
            # Usually a value after the label wins: ``кв 1``. The exception is
            # ``4 подъезд 9 этаж`` where 9 clearly belongs to the next label.
            next_label = re.match(
                r"\s*(?:квартира|кв|пәтер|flat|kv|подъезд|подьезд|под|"
                r"кіреберіс|этаж|эт|floor|қабат|дом|д|үй)\b",
                text[direct.end() :],
                re.IGNORECASE,
            )
            if next_label:
                match = reverse
        return _strip_value(match.group("value")), _remove_span(text, match.span())
    return None, text


def _extract_locations(segments: list[str]) -> tuple[dict[str, str | None], list[str]]:
    locations: dict[str, str | None] = {
        "province": None,
        "city": None,
        "district": None,
    }
    address_segments: list[str] = []

    for segment in segments:
        is_location = False
        parts = re.split(r"(?<!\d)/(?!\d)", segment)
        for part in parts:
            candidate = _strip_value(part)
            if not candidate:
                continue

            province_match = re.fullmatch(
                r"(?P<name>.+?)\s+(?P<label>область|обл\.?|облысы)",
                candidate,
                re.IGNORECASE,
            )
            if province_match:
                name = _strip_value(province_match.group("name"))
                if province_match.group("label").casefold() == "облысы":
                    locations["province"] = PROVINCE_ALIASES.get(
                        name.casefold(), f"{name} область"
                    )
                else:
                    locations["province"] = f"{name} область"
                is_location = True
                continue

            city_match = re.fullmatch(
                r"(?:город|г\.?)\s*(?P<name>.+)", candidate, re.IGNORECASE
            )
            if not city_match:
                city_match = re.fullmatch(
                    r"(?P<name>.+?)\s+(?:қаласы|қала)", candidate, re.IGNORECASE
                )
            if city_match:
                if locations["city"] is None:
                    locations["city"] = _canonical_city(city_match.group("name"))
                is_location = True
                continue

            district_match = re.fullmatch(
                r"(?P<name>.+?)\s+(?:район|р-н|ауданы|аудан)",
                candidate,
                re.IGNORECASE,
            )
            if district_match:
                if locations["district"] is None:
                    locations["district"] = _strip_value(district_match.group("name"))
                is_location = True
                continue

            known_city = CITY_ALIASES.get(candidate.casefold())
            if known_city:
                if locations["city"] is None:
                    locations["city"] = known_city
                is_location = True

        if not is_location:
            address_segments.append(segment)

    city = locations["city"]
    if city and city.casefold() in REPUBLICAN_CITIES:
        locations["province"] = REPUBLICAN_CITIES[city.casefold()]

    return locations, address_segments


def _typed_street(segment: str) -> tuple[str, str] | None:
    match = PREFIXED_STREET_RE.fullmatch(segment) or SUFFIXED_STREET_RE.fullmatch(
        segment
    )
    if not match:
        return None
    name = _strip_value(match.group("name"))
    if not name:
        return None
    return _canonical_type(match.group("type")), name


def _split_trailing_house(value: str) -> tuple[str, str | None]:
    match = TRAILING_HOUSE_RE.fullmatch(value)
    if not match:
        return _strip_value(value), None
    return _strip_value(match.group("name")), _strip_value(match.group("house"))


def recalculate_confidence(result: AddressResult) -> float:
    if not _clean_source(result.raw_address):
        return 0.0
    score = 0.05
    score += 0.10 if result.province else 0.0
    score += 0.15 if result.city else 0.0
    score += 0.25 if result.street_name else 0.0
    score += 0.25 if result.house else 0.0
    score += 0.07 if result.apartment else 0.0
    score += 0.04 if result.entrance else 0.0
    score += 0.04 if result.floor else 0.0
    score += 0.03 if result.district else 0.0
    score += 0.02 if result.living_area else 0.0
    return round(min(score, 0.99), 2)


def parse_address(record: AddressInput) -> AddressResult:
    """Parse one record without network or database dependencies."""

    source = _clean_source(record.raw_address)
    prepared = _prepare(source)
    initial_segments = [
        _strip_value(item)
        for item in re.split(r"[,;]+", prepared)
        if _strip_value(item)
    ]
    locations, address_segments = _extract_locations(initial_segments)
    working = ", ".join(address_segments)

    apartment, working = _extract_detail(
        working, r"квартира|кв|пәтер|flat|kv", NUMBER_VALUE
    )
    entrance, working = _extract_detail(
        working, r"подъезд|подьезд|под|кіреберіс", NUMBER_VALUE
    )
    floor, working = _extract_detail(working, r"этаж|эт|floor|қабат", NUMBER_VALUE)
    house, working = _extract_detail(working, r"дом|д|үй", HOUSE_VALUE)

    landmark = None
    landmark_match = LANDMARK_RE.search(working)
    if landmark_match:
        landmark = _strip_value(landmark_match.group())
        working = _remove_span(working, landmark_match.span())

    remaining = [
        _strip_value(item)
        for item in re.split(r"[,;]+", working)
        if _strip_value(item)
    ]

    if house is None:
        for index, segment in enumerate(remaining):
            if ONLY_HOUSE_RE.fullmatch(segment):
                house = segment
                remaining.pop(index)
                break

    living_area = None
    typed: list[tuple[str, str]] = []
    untyped: list[str] = []
    for segment in remaining:
        living_match = LIVING_AREA_RE.fullmatch(segment)
        if living_match:
            living_area = living_area or _strip_value(living_match.group("name"))
            continue
        suffix_with_house = SUFFIXED_STREET_WITH_HOUSE_RE.fullmatch(segment)
        if suffix_with_house:
            typed.append(
                (
                    _canonical_type(suffix_with_house.group("type")),
                    _strip_value(suffix_with_house.group("name")),
                )
            )
            house = house or _strip_value(suffix_with_house.group("house"))
            continue
        street = _typed_street(segment)
        if street:
            typed.append(street)
        else:
            untyped.append(segment)

    street_type = None
    street_name = None
    road_types = {"улица", "проспект", "переулок"}
    road = next((item for item in typed if item[0] in road_types), None)
    if road:
        street_type, street_name = road
        if living_area is None:
            area = next(
                (item for item in typed if item[0] in {"микрорайон", "квартал"}),
                None,
            )
            if area:
                living_area = area[1]
    elif typed:
        street_type, street_name = typed[0]
    elif untyped:
        street_name = untyped[0]

    if street_name and house is None and street_type not in {"микрорайон", "квартал"}:
        street_name, house = _split_trailing_house(street_name)
    if street_name and not re.search(
        r"[0-9A-Za-zА-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІі]", street_name
    ):
        street_name = None

    result = AddressResult(
        id=record.id,
        raw_address=record.raw_address,
        province=locations["province"],
        city=locations["city"],
        district=locations["district"],
        living_area=living_area,
        street_type=street_type,
        street_name=street_name,
        house=house,
        apartment=apartment,
        entrance=entrance,
        floor=floor,
        landmark=landmark,
        confidence=0.0,
    )
    result.confidence = recalculate_confidence(result)
    return result


def parse_address_safely(record: AddressInput) -> AddressResult:
    """Always return one result for one source record."""

    try:
        return parse_address(record)
    except Exception:
        logger.exception("Не удалось разобрать запись id=%s", record.id)
        return AddressResult(id=record.id, raw_address=record.raw_address, confidence=0.0)
