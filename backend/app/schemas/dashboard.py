from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    total_addresses: int = Field(description="Всего обработанных адресов")
    geocoded_addresses: int = Field(description="Адресов с найденными координатами")
    pending_review: int = Field(description="Адресов, ожидающих ручной проверки")
    average_confidence: float = Field(description="Средняя уверенность парсера от 0 до 1")
    geocoding_rate: float = Field(description="Доля адресов с координатами в процентах")
    total_batches: int = Field(description="Всего массовых задач")
    completed_batches: int = Field(description="Завершенных массовых задач")
