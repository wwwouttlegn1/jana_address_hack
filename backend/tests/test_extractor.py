from app.parser.extractor import extract_components
from app.parser.normalizer import normalize_address


def test_extracts_russian_address_components() -> None:
    extracted = extract_components(
        normalize_address(
            "Казахстан, г. Алматы, ул. Абая, д. 10, корп. 2, кв. 15, 050000"
        )
    )

    assert extracted.components["country"] == "Казахстан"
    assert extracted.components["city"] == "алматы"
    assert extracted.components["street"] == "абая"
    assert extracted.components["street_type"] == "улица"
    assert extracted.components["house"] == "10"
    assert extracted.components["building"] == "2"
    assert extracted.components["apartment"] == "15"
    assert extracted.components["postal_code"] == "050000"


def test_extracts_kazakh_suffixes_and_bare_house() -> None:
    extracted = extract_components(
        normalize_address("Қызылорда облысы, Қызылорда қаласы, Абай көшесі 25")
    )

    assert extracted.components["region"] == "қызылорда"
    assert extracted.components["city"] == "қызылорда"
    assert extracted.components["street"] == "абай"
    assert extracted.components["street_type"] == "көше"
    assert extracted.components["house"] == "25"
