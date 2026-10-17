from app.parser.normalizer import canonicalize_name, normalize_address


def test_normalize_address_handles_unicode_spaces_and_separators() -> None:
    value = "  Қазақстан\u00a0;  Қызылорда\n Абай көшесі 25  "

    assert normalize_address(value) == "қазақстан, қызылорда, абай көшесі 25"


def test_canonicalize_name_removes_punctuation() -> None:
    assert canonicalize_name("  Ул. Абая! ") == "ул абая"
