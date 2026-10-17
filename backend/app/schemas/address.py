from __future__ import annotations

import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


AddressText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=2_000)]


class AddressComponents(BaseModel):
    country: str | None = Field(default=None, description="Страна")
    region: str | None = Field(default=None, description="Область или регион")
    district: str | None = Field(default=None, description="Район")
    city: str | None = Field(default=None, description="Город")
    settlement: str | None = Field(default=None, description="Село или населенный пункт")
    street: str | None = Field(default=None, description="Улица, проспект или микрорайон")
    street_type: str | None = Field(
        default=None, description="Тип улицы: улица, проспект, микрорайон и т.д."
    )
    house: str | None = Field(default=None, description="Номер дома")
    block: str | None = Field(default=None, description="Блок")
    building: str | None = Field(default=None, description="Корпус или строение")
    apartment: str | None = Field(default=None, description="Квартира")
    entrance: str | None = Field(default=None, description="Подъезд")
    floor: str | None = Field(default=None, description="Этаж")
    office: str | None = Field(default=None, description="Офис")
    postal_code: str | None = Field(default=None, description="Шестизначный почтовый индекс")

    model_config = ConfigDict(extra="forbid")

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, value: str | None) -> str | None:
        if value is not None and (not value.isdigit() or len(value) != 6):
            raise ValueError("postal_code must contain exactly 6 digits")
        return value


class ParseAddressRequest(BaseModel):
    address: AddressText
    external_id: str | None = Field(default=None, max_length=255)
    persist: bool = True

    model_config = ConfigDict(extra="forbid")


class ResolveAddressRequest(BaseModel):
    address: AddressText = Field(
        description="Адрес в свободной форме на русском или казахском языке",
        examples=["Казахстан, г. Алматы, проспект Абая, д. 10, кв. 15"],
    )
    external_id: str | None = Field(
        default=None,
        max_length=255,
        description="Необязательный ID заказа, клиента или строки из вашей системы",
        examples=["order-42"],
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "address": "Казахстан, г. Алматы, проспект Абая, д. 10, кв. 15",
                "external_id": "order-42",
            }
        },
    )


class BatchAddressItem(BaseModel):
    address: AddressText
    external_id: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(extra="forbid")


class BatchParseRequest(BaseModel):
    items: list[BatchAddressItem] = Field(min_length=1)
    persist: bool = True

    model_config = ConfigDict(extra="forbid")


class GeoLocation(BaseModel):
    latitude: float = Field(description="Широта")
    longitude: float = Field(description="Долгота")
    display_name: str = Field(description="Адрес, найденный геокодером")
    precision: Literal["house", "street", "settlement", "region", "unknown"] = Field(
        description="Ожидаемая точность координат"
    )
    provider: str = Field(description="Источник координат")
    map_url: str = Field(description="Ссылка на точку на карте OpenStreetMap")
    attribution: str = Field(description="Обязательная атрибуция источника данных")
    osm_type: str | None = None
    osm_id: int | None = None


class ParseAddressResult(BaseModel):
    record_id: uuid.UUID | None = None
    external_id: str | None = None
    raw_address: str
    normalized_address: str
    components: AddressComponents
    resolved_reference_ids: dict[str, int] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool
    warnings: list[str] = Field(default_factory=list)
    geocoding_status: Literal["found", "not_found", "disabled", "error"] = Field(
        description="Результат поиска координат"
    )
    location: GeoLocation | None = Field(
        default=None, description="Координаты; null, если адрес не найден"
    )


class BatchParseResponse(BaseModel):
    total: int
    success_count: int
    review_count: int
    error_count: int
    results: list[ParseAddressResult]
