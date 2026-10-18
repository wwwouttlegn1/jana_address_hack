import io
import json
import uuid

import pytest


@pytest.mark.asyncio
async def test_health(client) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"


@pytest.mark.asyncio
async def test_single_address_uses_exact_challenge_contract(client) -> None:
    raw_address = "город Алматы/Алматы қаласы, Мкр Аксай 3а, 59, кв 70"
    response = await client.post(
        "/api/v1/parse",
        json={"id": "rec_00417", "raw_address": raw_address},
    )

    assert response.status_code == 200
    payload = response.json()
    uuid.UUID(payload.pop("record_id"))
    assert payload == {
        "id": "rec_00417",
        "raw_address": raw_address,
        "province": "Алматы",
        "city": "Алматы",
        "district": None,
        "living_area": None,
        "street_type": "микрорайон",
        "street_name": "Аксай 3а",
        "house": "59",
        "apartment": "70",
        "entrance": None,
        "floor": None,
        "landmark": None,
        "confidence": 0.87,
        "needs_review": False,
    }


@pytest.mark.asyncio
async def test_batch_preserves_count_order_and_uncertain_record(client) -> None:
    response = await client.post(
        "/api/v1/parse/batch",
        json=[
            {"id": "first", "raw_address": "66квартал 12дом 69квартира"},
            {"id": "second", "raw_address": "???"},
            {"id": "third", "raw_address": "Назарбаева8 flat 191"},
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == ["first", "second", "third"]
    assert payload[0]["street_type"] == "квартал"
    assert payload[0]["house"] == "12"
    assert payload[0]["apartment"] == "69"
    assert payload[1]["street_name"] is None
    assert payload[1]["confidence"] == 0.05
    assert payload[1]["needs_review"] is True
    assert payload[2]["street_name"] == "Назарбаева"
    assert payload[2]["house"] == "8"
    assert payload[2]["apartment"] == "191"


@pytest.mark.asyncio
async def test_json_file_upload(client) -> None:
    content = json.dumps(
        [{"id": "1", "raw_address": "Ул .Курильская 9 кв 1"}],
        ensure_ascii=False,
    ).encode("utf-8")

    response = await client.post(
        "/api/v1/parse/file",
        files={"file": ("addresses.json", io.BytesIO(content), "application/json")},
    )

    assert response.status_code == 200
    assert response.json()[0]["street_name"] == "Курильская"
    assert response.json()[0]["house"] == "9"


@pytest.mark.asyncio
async def test_saved_records_can_be_loaded_and_corrected(client) -> None:
    created = (
        await client.post(
            "/api/v1/parse",
            json={"id": "saved-1", "raw_address": "Назарбаева8 flat 191"},
        )
    ).json()

    records_response = await client.get("/api/v1/records")
    assert records_response.status_code == 200
    assert records_response.json()[0]["record_id"] == created["record_id"]

    correction_response = await client.patch(
        f"/api/v1/records/{created['record_id']}",
        json={"city": "Алматы", "district": "Медеу ауданы"},
    )
    assert correction_response.status_code == 200
    corrected = correction_response.json()
    assert corrected["city"] == "Алматы"
    assert corrected["district"] == "Медеу ауданы"
    assert corrected["needs_review"] is False

    reloaded = (await client.get("/api/v1/records")).json()[0]
    assert reloaded["city"] == "Алматы"
    assert reloaded["district"] == "Медеу ауданы"


@pytest.mark.asyncio
async def test_swagger_contains_only_clear_public_pipeline(client) -> None:
    schema = (await client.get("/openapi.json")).json()

    assert schema["openapi"] == "3.0.3"
    assert set(schema["paths"]) == {
        "/api/v1/parse",
        "/api/v1/parse/batch",
        "/api/v1/parse/file",
        "/api/v1/records",
        "/api/v1/records/{record_id}",
        "/api/v1/health",
    }
    assert "основной метод для жюри" in schema["paths"]["/api/v1/parse/batch"][
        "post"
    ]["summary"]
