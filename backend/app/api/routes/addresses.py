import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.schemas.address import (
    BatchParseRequest,
    BatchParseResponse,
    ParseAddressRequest,
    ParseAddressResult,
    ResolveAddressRequest,
)
from app.services.address_service import AddressService, record_to_result
from app.storage.database import get_session


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/resolve",
    response_model=ParseAddressResult,
    status_code=status.HTTP_200_OK,
    summary="Нормализовать адрес и получить координаты",
    description=(
        "Главный запрос кейса JANA ADDRESS. Принимает адрес в свободной форме, "
        "выделяет компоненты, оценивает качество и ищет координаты в Казахстане. "
        "Результат сохраняется для последующей проверки."
    ),
    response_description="Структурированный адрес, оценка качества и координаты",
    responses={
        422: {"description": "Адрес пустой, слишком короткий или тело запроса некорректно"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def resolve_address(
    request: ResolveAddressRequest,
    session: AsyncSession = Depends(get_session),
) -> ParseAddressResult:
    result = await AddressService(session).parse(
        ParseAddressRequest(
            address=request.address,
            external_id=request.external_id,
            persist=True,
        )
    )
    await session.commit()
    return result


@router.post(
    "/parse",
    response_model=ParseAddressResult,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def parse_address_legacy(
    request: ParseAddressRequest,
    session: AsyncSession = Depends(get_session),
) -> ParseAddressResult:
    result = await AddressService(session).parse(request)
    await session.commit()
    return result


@router.post("/parse/batch", response_model=BatchParseResponse, include_in_schema=False)
async def parse_batch(
    request: BatchParseRequest,
    session: AsyncSession = Depends(get_session),
) -> BatchParseResponse:
    settings = get_settings()
    if len(request.items) > settings.max_batch_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Максимальный размер пакета: {settings.max_batch_size}",
        )

    service = AddressService(session)
    results = []
    errors = 0
    for item in request.items:
        try:
            async with session.begin_nested():
                results.append(
                    await service.parse(
                        ParseAddressRequest(
                            address=item.address,
                            external_id=item.external_id,
                            persist=request.persist,
                        )
                    )
                )
        except Exception:
            logger.exception("Batch parse failed for external_id=%s", item.external_id)
            errors += 1
    await session.commit()
    return BatchParseResponse(
        total=len(request.items),
        success_count=len(results),
        review_count=sum(item.needs_review for item in results),
        error_count=errors,
        results=results,
    )


@router.get("/{record_id}", response_model=ParseAddressResult, include_in_schema=False)
async def get_address_record(
    record_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ParseAddressResult:
    record = await AddressService(session).get(record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Адрес не найден")
    return record_to_result(record)
