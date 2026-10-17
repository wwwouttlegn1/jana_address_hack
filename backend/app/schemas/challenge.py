from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AddressInput(BaseModel):
    """One source record from the challenge dataset."""

    id: str = Field(description="Source record identifier", examples=["rec_00417"])
    raw_address: str = Field(
        description="Address exactly as entered by the client",
        examples=["город Алматы/Алматы қаласы, Мкр Аксай 3а, 59, кв 70"],
        max_length=2_000,
    )

    model_config = ConfigDict(extra="ignore")


class AddressResult(BaseModel):
    """Flat response contract required by the JANA ADDRESS case."""

    id: str
    raw_address: str
    province: str | None = None
    city: str | None = None
    district: str | None = None
    living_area: str | None = None
    street_type: str | None = None
    street_name: str | None = None
    house: str | None = None
    apartment: str | None = None
    entrance: str | None = None
    floor: str | None = None
    landmark: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "rec_00417",
                "raw_address": (
                    "город Алматы/Алматы қаласы, Мкр Аксай 3а, 59, кв 70"
                ),
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
            }
        }
    )
