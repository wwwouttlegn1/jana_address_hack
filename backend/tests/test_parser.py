import pytest

from app.parser.engine import AddressParser


@pytest.mark.asyncio
async def test_parser_returns_confident_structured_result() -> None:
    result = await AddressParser().parse(
        "Казахстан, г. Алматы, ул. Абая, д. 10, кв. 15, 050000"
    )

    assert result.components["city"] == "алматы"
    assert result.components["street"] == "абая"
    assert result.components["house"] == "10"
    assert result.confidence >= 0.72
    assert result.needs_review is False


@pytest.mark.asyncio
async def test_parser_marks_incomplete_address_for_review() -> None:
    result = await AddressParser().parse("г. Алматы")

    assert result.needs_review is True
    assert "Не определена улица" in result.warnings
    assert "Не определен номер дома" in result.warnings
