from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.dashboard import DashboardStatsResponse
from app.storage.database import get_session
from app.storage.models import AddressRecord, BatchJob, BatchStatus


router = APIRouter()


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Получить показатели проекта",
    description=(
        "Готовые цифры для dashboard и демонстрации жюри: сколько адресов обработано, "
        "сколько найдено на карте и сколько требует проверки."
    ),
)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_session),
) -> DashboardStatsResponse:
    total_addresses = await session.scalar(select(func.count(AddressRecord.id))) or 0
    geocoded_addresses = (
        await session.scalar(
            select(func.count(AddressRecord.id)).where(
                AddressRecord.geocoding_status == "found"
            )
        )
        or 0
    )
    pending_review = (
        await session.scalar(
            select(func.count(AddressRecord.id)).where(AddressRecord.needs_review.is_(True))
        )
        or 0
    )
    average_confidence = await session.scalar(select(func.avg(AddressRecord.confidence))) or 0.0
    total_batches = await session.scalar(select(func.count(BatchJob.id))) or 0
    completed_batches = (
        await session.scalar(
            select(func.count(BatchJob.id)).where(
                BatchJob.status == BatchStatus.completed.value
            )
        )
        or 0
    )
    geocoding_rate = (
        round((geocoded_addresses / total_addresses) * 100, 1) if total_addresses else 0.0
    )
    return DashboardStatsResponse(
        total_addresses=total_addresses,
        geocoded_addresses=geocoded_addresses,
        pending_review=pending_review,
        average_confidence=round(float(average_confidence), 3),
        geocoding_rate=geocoding_rate,
        total_batches=total_batches,
        completed_batches=completed_batches,
    )
