import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.review import (
    ReviewItemResponse,
    ReviewListResponse,
    ReviewStatsResponse,
    ReviewUpdateRequest,
)
from app.storage.database import get_session
from app.storage.review_repository import ReviewRepository


router = APIRouter()


@router.get(
    "",
    response_model=ReviewListResponse,
    summary="Показать адреса, требующие проверки",
    description=(
        "Здесь находятся неполные, неоднозначные или неуверенно распознанные адреса. "
        "По умолчанию возвращаются только ожидающие решения."
    ),
)
async def list_reviews(
    review_status: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> ReviewListResponse:
    if review_status not in {None, "pending", "approved", "corrected", "rejected"}:
        raise HTTPException(status_code=422, detail="Неизвестный статус проверки")
    records, total = await ReviewRepository(session).list(
        status=review_status, page=page, page_size=page_size
    )
    return ReviewListResponse(
        items=[ReviewItemResponse.model_validate(record) for record in records],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=ReviewStatsResponse, include_in_schema=False)
async def review_stats(
    session: AsyncSession = Depends(get_session),
) -> ReviewStatsResponse:
    return ReviewStatsResponse.model_validate(await ReviewRepository(session).stats())


@router.get("/{record_id}", response_model=ReviewItemResponse, include_in_schema=False)
async def get_review(
    record_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ReviewItemResponse:
    record = await ReviewRepository(session).get(record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")
    return ReviewItemResponse.model_validate(record)


@router.patch(
    "/{record_id}",
    response_model=ReviewItemResponse,
    summary="Подтвердить, исправить или отклонить адрес",
    description=(
        "Для `approved` достаточно статуса и комментария. Для `corrected` передайте "
        "исправленные компоненты адреса."
    ),
)
async def update_review(
    record_id: uuid.UUID,
    request: ReviewUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> ReviewItemResponse:
    repository = ReviewRepository(session)
    record = await repository.get(record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")
    if record.review_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Запись уже прошла ручную проверку",
        )
    return ReviewItemResponse.model_validate(await repository.update(record, request))
