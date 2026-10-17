import re
import unicodedata


WHITESPACE_RE = re.compile(r"\s+")
SEPARATOR_RE = re.compile(r"\s*[,;|]+\s*")
DOT_SPACING_RE = re.compile(r"\s*\.\s*")
NON_WORD_RE = re.compile(r"[^0-9a-zа-яәғқңөұүһіё\s-]", re.IGNORECASE)


def normalize_address(value: str) -> str:
    """Return a stable, human-readable representation used by the parser."""

    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\u00a0", " ").replace("\n", ", ").replace("\r", " ")
    value = value.replace("“", '"').replace("”", '"').replace("’", "'")
    value = SEPARATOR_RE.sub(", ", value)
    value = WHITESPACE_RE.sub(" ", value)
    return value.strip(" ,").casefold()


def canonicalize_name(value: str) -> str:
    value = normalize_address(value)
    value = DOT_SPACING_RE.sub(" ", value)
    value = NON_WORD_RE.sub(" ", value)
    return WHITESPACE_RE.sub(" ", value).strip()
