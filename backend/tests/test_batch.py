import json

import pytest

from app.api.routes.batches import _parse_uploaded_file


def test_parse_json_upload() -> None:
    content = json.dumps(
        {"items": [{"external_id": 7, "address": "г. Алматы, ул. Абая, д. 10"}]}
    ).encode()

    items, source_type = _parse_uploaded_file("addresses.json", content)

    assert source_type == "json"
    assert items[0].external_id == "7"
    assert items[0].address.endswith("д. 10")


def test_parse_csv_upload() -> None:
    content = "external_id,address\nabc,г. Алматы ул. Абая д. 10\n".encode("utf-8")

    items, source_type = _parse_uploaded_file("addresses.csv", content)

    assert source_type == "csv"
    assert items[0].external_id == "abc"


def test_rejects_unknown_upload_format() -> None:
    with pytest.raises(ValueError, match="Поддерживаются"):
        _parse_uploaded_file("addresses.txt", b"address")
