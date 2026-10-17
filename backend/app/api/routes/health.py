from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.storage.database import ping_database


router = APIRouter()


@router.get(
    "",
    summary="Проверить готовность сервера",
    description="Проверяет, что FastAPI работает и PostgreSQL принимает запросы.",
)
async def health() -> dict[str, str]:
    try:
        await ping_database()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="База данных недоступна",
        ) from exc
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "database": "ok",
    }
