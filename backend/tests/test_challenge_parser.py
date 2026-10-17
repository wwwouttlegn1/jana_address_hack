import pytest

from app.parser.challenge import parse_address
from app.schemas.challenge import AddressInput


@pytest.mark.parametrize(
    ("raw_address", "expected"),
    [
        (
            "66квартал 12дом 69квартира",
            {
                "street_type": "квартал",
                "street_name": "66",
                "house": "12",
                "apartment": "69",
            },
        ),
        (
            "Ул .Курильская 9 кв 1",
            {
                "street_type": "улица",
                "street_name": "Курильская",
                "house": "9",
                "apartment": "1",
            },
        ),
        (
            "Туран 55/6 магазин Береке 4подьезд 9этаж",
            {
                "street_name": "Туран",
                "house": "55/6",
                "landmark": "магазин Береке",
                "entrance": "4",
                "floor": "9",
            },
        ),
        (
            "Нурсити 2 микрорайон 11дом 5 подьезд 239 кв",
            {
                "street_type": "микрорайон",
                "street_name": "Нурсити 2",
                "house": "11",
                "entrance": "5",
                "apartment": "239",
            },
        ),
        (
            "Қызылорда облысы, Қызылорда қаласы, Абай көшесі 25, 7 пәтер",
            {
                "province": "Кызылординская область",
                "city": "Кызылорда",
                "street_type": "улица",
                "street_name": "Абай",
                "house": "25",
                "apartment": "7",
            },
        ),
    ],
)
def test_parser_handles_case_examples(raw_address: str, expected: dict[str, str]) -> None:
    result = parse_address(AddressInput(id="test", raw_address=raw_address))

    for field, value in expected.items():
        assert getattr(result, field) == value


def test_separate_living_area_and_street() -> None:
    result = parse_address(
        AddressInput(
            id="1",
            raw_address=(
                "г. Алматы, Ауэзовский район, ЖК Томирис, "
                "ул. Жандосова 12а, kv 12"
            ),
        )
    )

    assert result.province == "Алматы"
    assert result.city == "Алматы"
    assert result.district == "Ауэзовский"
    assert result.living_area == "Томирис"
    assert result.street_name == "Жандосова"
    assert result.house == "12а"
    assert result.apartment == "12"


def test_unparseable_record_is_not_dropped() -> None:
    result = parse_address(AddressInput(id="bad", raw_address="???"))

    assert result.id == "bad"
    assert result.raw_address == "???"
    assert result.street_name is None
    assert result.confidence < 0.2
