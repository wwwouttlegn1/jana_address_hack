from __future__ import annotations

import csv
import io
import json
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import Response
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.schemas.address import BatchAddressItem
from app.schemas.batch import (
    BatchCreateRequest,
    BatchJobResponse,
    BatchListResponse,
    BatchResultsResponse,
)
from app.services.address_service import record_to_result
from app.services.batch_service import (
    BatchNotFoundError,
    BatchService,
    process_batch_job,
)
from app.services.export_service import export_csv, export_json
from app.storage.database import get_session
from app.storage.models import AddressRecord, BatchStatus


router = APIRouter()


@router.get(
    "",
    response_model=BatchListResponse,
    summary="Показать последние массовые задачи",
    description="Используется страницей истории и позволяет вернуться к результатам после перезапуска.",
)
async def list_batches(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> BatchListResponse:
    items, total = await BatchService(session).list(page=page, page_size=page_size)
    return BatchListResponse(
        items=[BatchJobResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=BatchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Создать массовую обработку из JSON",
    description=(
        "Передайте список адресов. Сервер сразу вернет ID задачи, а нормализация "
        "и поиск координат продолжатся в фоне."
    ),
    response_description="Созданная фоновая задача",
)
async def create_batch(
    request: BatchCreateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> BatchJobResponse:
    items = [BatchAddressItem(address=value) for value in request.items]
    try:
        batch = await BatchService(session).create(
            items, source_type="json", source_name=request.source_name
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    background_tasks.add_task(process_batch_job, batch.id)
    return BatchJobResponse.model_validate(batch)


@router.post(
    "/upload",
    response_model=BatchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Загрузить JSON или CSV с адресами",
    description=(
        "Загрузите файл `.json` или `.csv`. CSV должен содержать колонку `address`; "
        "колонка `external_id` необязательна. Максимальный размер файла — 10 МБ."
    ),
    response_description="Созданная задача обработки файла",
)
async def upload_batch(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> BatchJobResponse:
    settings = get_settings()
    content = await file.read(settings.max_upload_bytes + 1)
    await file.close()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл больше {settings.max_upload_bytes} байт",
        )
    try:
        items, source_type = _parse_uploaded_file(file.filename or "upload.json", content)
        batch = await BatchService(session).create(
            items, source_type=source_type, source_name=Path(file.filename or "upload").name
        )
    except (UnicodeDecodeError, json.JSONDecodeError, csv.Error, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    background_tasks.add_task(process_batch_job, batch.id)
    return BatchJobResponse.model_validate(batch)


@router.get(
    "/{batch_id}",
    response_model=BatchJobResponse,
    summary="Посмотреть прогресс массовой обработки",
    description="Подставьте ID, полученный при создании задачи или загрузке файла.",
)
async def get_batch(
    batch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> BatchJobResponse:
    try:
        batch = await BatchService(session).get(batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return BatchJobResponse.model_validate(batch)


@router.get(
    "/{batch_id}/results",
    response_model=BatchResultsResponse,
    summary="Получить обработанные адреса",
    description="Возвращает страницу нормализованных адресов вместе с координатами.",
)
async def get_batch_results(
    batch_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> BatchResultsResponse:
    service = BatchService(session)
    try:
        batch = await service.get(batch_id)
        records, total = await service.get_records(batch_id, page=page, page_size=page_size)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return BatchResultsResponse(
        batch=BatchJobResponse.model_validate(batch),
        items=[record_to_result(record) for record in records if record.normalized_address],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{batch_id}/export",
    summary="Скачать результаты в JSON или CSV",
    description="Укажите `format=json` или `format=csv`.",
)
async def export_batch(
    batch_id: uuid.UUID,
    format: str = Query(default="json", pattern="^(json|csv)$"),
    session: AsyncSession = Depends(get_session),
) -> Response:
    try:
        await BatchService(session).get(batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    records = list(
        (
            await session.scalars(
                select(AddressRecord)
                .where(AddressRecord.batch_id == batch_id)
                .order_by(AddressRecord.sequence)
            )
        ).all()
    )
    if format == "csv":
        content = export_csv(records)
        media_type = "text/csv; charset=utf-8"
    else:
        content = export_json(records)
        media_type = "application/json"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="batch-{batch_id}.{format}"'},
    )


@router.post(
    "/{batch_id}/retry",
    response_model=BatchJobResponse,
    status_code=202,
    include_in_schema=False,
)
async def retry_batch(
    batch_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> BatchJobResponse:
    try:
        batch = await BatchService(session).get(batch_id)
    except BatchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if batch.status == BatchStatus.processing.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пакет уже обрабатывается")
    if batch.status == BatchStatus.completed.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пакет уже завершен")
    batch.status = BatchStatus.queued.value
    batch.error_message = None
    await session.execute(
        update(AddressRecord)
        .where(
            AddressRecord.batch_id == batch_id,
            AddressRecord.error_message.is_not(None),
        )
        .values(error_message=None)
    )
    await session.commit()
    background_tasks.add_task(process_batch_job, batch.id)
    return BatchJobResponse.model_validate(batch)


def _parse_uploaded_file(filename: str, content: bytes) -> tuple[list[BatchAddressItem], str]:
    suffix = Path(filename).suffix.casefold()
    if suffix == ".json":
        payload = json.loads(content.decode("utf-8-sig"))
        raw_items = payload.get("items") if isinstance(payload, dict) else payload
        if not isinstance(raw_items, list):
            raise ValueError("JSON должен быть массивом или объектом с массивом items")
        items: list[BatchAddressItem] = []
        for index, item in enumerate(raw_items, start=1):
            if isinstance(item, str):
                items.append(BatchAddressItem(address=item))
            elif isinstance(item, dict) and "address" in item:
                items.append(
                    BatchAddressItem(
                        address=item["address"],
                        external_id=str(item["external_id"]) if item.get("external_id") is not None else None,
                    )
                )
            else:
                raise ValueError(f"Некорректная запись JSON под номером {index}")
        return items, "json"

    if suffix == ".csv":
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or "address" not in reader.fieldnames:
            raise ValueError("CSV должен содержать колонку address")
        items = [
            BatchAddressItem(
                address=row["address"],
                external_id=row.get("external_id") or None,
            )
            for row in reader
            if row.get("address", "").strip()
        ]
        return items, "csv"

    raise ValueError("Поддерживаются только файлы .json и .csv")
