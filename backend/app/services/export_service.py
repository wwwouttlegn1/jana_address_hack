from __future__ import annotations

import csv
import io
import json

from app.services.address_service import record_to_result
from app.storage.models import AddressRecord


def export_json(records: list[AddressRecord]) -> bytes:
    payload = [record_to_result(record).model_dump(mode="json") for record in records]
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def export_csv(records: list[AddressRecord]) -> bytes:
    output = io.StringIO(newline="")
    fieldnames = [
        "record_id",
        "external_id",
        "raw_address",
        "normalized_address",
        "confidence",
        "needs_review",
        "geocoding_status",
        "latitude",
        "longitude",
        "geocoding_precision",
        "map_url",
        "country",
        "region",
        "district",
        "city",
        "settlement",
        "street",
        "house",
        "building",
        "block",
        "apartment",
        "postal_code",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for record in records:
        result = record_to_result(record)
        row = {
            "record_id": str(result.record_id),
            "external_id": result.external_id,
            "raw_address": result.raw_address,
            "normalized_address": result.normalized_address,
            "confidence": result.confidence,
            "needs_review": result.needs_review,
            "geocoding_status": result.geocoding_status,
            "latitude": result.location.latitude if result.location else None,
            "longitude": result.location.longitude if result.location else None,
            "geocoding_precision": result.location.precision if result.location else None,
            "map_url": result.location.map_url if result.location else None,
            **result.components.model_dump(),
        }
        writer.writerow({key: row.get(key) for key in fieldnames})
    return output.getvalue().encode("utf-8-sig")
