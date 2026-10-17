import pytest

from app.services.geocoding_service import GeocodingService


@pytest.mark.asyncio
async def test_geocoder_query_excludes_private_delivery_details(db_session) -> None:
    service = GeocodingService(db_session)

    query = service._build_public_query(
        {
            "country": "Казахстан",
            "city": "Алматы",
            "street": "Абая",
            "street_type": "улица",
            "house": "10",
            "apartment": "55",
            "entrance": "2",
            "floor": "7",
        }
    )

    assert query == "улица Абая 10, Алматы, Казахстан"
    assert "55" not in query


@pytest.mark.asyncio
async def test_geocoder_maps_provider_response(db_session, monkeypatch) -> None:
    service = GeocodingService(db_session)
    monkeypatch.setattr(service.settings, "geocoding_enabled", True)

    async def fake_request(_: str):
        return [
            {
                "lat": "43.238949",
                "lon": "76.889709",
                "display_name": "проспект Абая, Алматы, Казахстан",
                "osm_type": "way",
                "osm_id": 123,
                "addresstype": "road",
                "address": {"road": "проспект Абая", "city": "Алматы"},
            }
        ]

    monkeypatch.setattr(service, "_request", fake_request)
    outcome = await service.geocode(
        "г. алматы, проспект абая",
        {
            "country": "Казахстан",
            "city": "Алматы",
            "street": "Абая",
            "street_type": "проспект",
        },
    )

    assert outcome.status == "found"
    assert outcome.location is not None
    assert outcome.location.latitude == pytest.approx(43.238949)
    assert outcome.location.precision == "street"
    assert outcome.location.osm_id == 123


def test_geocoder_prefers_exact_house_number() -> None:
    candidates = [
        {
            "display_name": "109/10, проспект Абая, Алматы",
            "importance": 0.8,
            "address": {
                "house_number": "109/10",
                "road": "проспект Абая",
                "city": "Алматы",
            },
        },
        {
            "display_name": "10, проспект Абая, Алматы",
            "importance": 0.5,
            "address": {
                "house_number": "10",
                "road": "проспект Абая",
                "city": "Алматы",
            },
        },
    ]

    selected = GeocodingService._select_best(
        candidates,
        {"house": "10", "street": "Абая", "city": "Алматы"},
    )

    assert selected["address"]["house_number"] == "10"
