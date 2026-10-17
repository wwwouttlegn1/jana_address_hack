from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or `.env`."""

    app_name: str = "JANA ADDRESS API"
    app_version: str = "1.0.0"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+asyncpg://jana_address:jana_address_dev@localhost:5432/jana_address"
    )
    database_echo: bool = False
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=100)

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_allow_credentials: bool = True

    max_batch_size: int = Field(default=20_000, ge=1, le=20_000)
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1_024)
    batch_checkpoint_size: int = Field(default=100, ge=1, le=1_000)
    review_confidence_threshold: float = Field(default=0.72, ge=0.0, le=1.0)
    reference_match_threshold: float = Field(default=84.0, ge=0.0, le=100.0)

    geocoding_enabled: bool = True
    geocoder_base_url: str = "https://nominatim.openstreetmap.org"
    geocoder_user_agent: str = "JANA-ADDRESS-Hackathon/1.0"
    geocoder_timeout_seconds: float = Field(default=8.0, gt=0.0, le=30.0)
    geocoder_min_interval_seconds: float = Field(default=1.1, ge=1.0, le=10.0)

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", PROJECT_ROOT / "backend" / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
