import re


POSTAL_CODE_RE = re.compile(r"(?<!\d)(\d{6})(?!\d)")

LABELED_PATTERNS: dict[str, re.Pattern[str]] = {
    "apartment": re.compile(
        r"(?:^|\s)(?:кв(?:артира)?|пәтер)\.?\s*№?\s*([0-9]+[a-zа-я]?)\b",
        re.IGNORECASE,
    ),
    "office": re.compile(
        r"(?:^|\s)(?:оф(?:ис)?|кеңсе)\.?\s*№?\s*([0-9]+[a-zа-я]?)\b",
        re.IGNORECASE,
    ),
    "entrance": re.compile(
        r"(?:^|\s)(?:подъезд|под|кіреберіс)\.?\s*№?\s*([0-9]+)\b",
        re.IGNORECASE,
    ),
    "floor": re.compile(
        r"(?:^|\s)(?:этаж|эт|қабат)\.?\s*([0-9]+)\b",
        re.IGNORECASE,
    ),
    "building": re.compile(
        r"(?:^|\s)(?:корпус|корп|корп\.|строение|стр|ғимарат)\s*№?\s*([0-9]+[a-zа-я]?)\b",
        re.IGNORECASE,
    ),
    "block": re.compile(
        r"(?:^|\s)(?:блок|бл)\.?\s*№?\s*([0-9]+[a-zа-я]?)\b",
        re.IGNORECASE,
    ),
    "house": re.compile(
        r"(?:^|\s)(?:дом|д|д\.|үй)\s*№?\s*([0-9]+[a-zа-я]?(?:[/\-][0-9a-zа-я]+)?)\b",
        re.IGNORECASE,
    ),
}

BARE_HOUSE_RE = re.compile(r"^(.+?)\s+№?([0-9]+[a-zа-я]?(?:[/\-][0-9a-zа-я]+)?)$", re.IGNORECASE)
