from __future__ import annotations

import csv
import io
import json
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.parser.challenge import parse_address_safely
from app.reference.jana_repository import JanaReferenceRepository
from app.schemas.challenge import AddressCorrection, AddressInput, AddressResult
from app.services.challenge_record_service import ChallengeRecordService
from app.storage.database import get_session


router = APIRouter()
input_list_adapter = TypeAdapter(list[AddressInput])


async def _parse_many(
    items: list[AddressInput], session: AsyncSession
) -> list[AddressResult]:
    settings = get_settings()
    if len(items) > settings.max_batch_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Максимум записей в одном запросе: {settings.max_batch_size}",
        )
    results: list[AddressResult] = []
    repository = JanaReferenceRepository(session)
    records = ChallengeRecordService(session)
    for sequence, item in enumerate(items):
        parsed = parse_address_safely(item)
        enriched = await repository.enrich(parsed)
        results.append(await records.save(enriched, sequence=sequence))
    return results


@router.post(
    "/parse",
    response_model=AddressResult,
    summary="Разобрать один адрес",
    description=(
        "Принимает `id` и исходный адрес. Возвращает плоскую структуру из задания "
        "уточняет результат по справочнику и сохраняет запись в PostgreSQL."
    ),
)
async def parse_one(
    payload: AddressInput,
    session: AsyncSession = Depends(get_session),
) -> AddressResult:
    repository = JanaReferenceRepository(session)
    result = await repository.enrich(parse_address_safely(payload))
    result = await ChallengeRecordService(session).save(result)
    await session.commit()
    return result


@router.post(
    "/parse/batch",
    response_model=list[AddressResult],
    summary="Обработать JSON-массив адресов — основной метод для жюри",
    description=(
        "Принимает JSON-массив объектов `{id, raw_address}`. Порядок и количество "
        "результатов совпадают со входом: сомнительный адрес не пропускается, а "
        "возвращается с `null` в ненайденных полях и низким `confidence`."
    ),
)
async def parse_batch(
    payload: list[AddressInput],
    session: AsyncSession = Depends(get_session),
) -> list[AddressResult]:
    results = await _parse_many(payload, session)
    await session.commit()
    return results


@router.post(
    "/parse/file",
    response_model=list[AddressResult],
    summary="Загрузить JSON или CSV",
    description=(
        "Для интерфейса оператора. JSON должен содержать массив записей, CSV — "
        "колонки `id` и `raw_address`."
    ),
)
async def parse_file(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> list[AddressResult]:
    settings = get_settings()
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Файл превышает допустимый размер",
        )

    filename = (file.filename or "").casefold()
    try:
        text = content.decode("utf-8-sig")
        if filename.endswith(".json"):
            raw_items = json.loads(text)
            if isinstance(raw_items, dict) and "items" in raw_items:
                raw_items = raw_items["items"]
        elif filename.endswith(".csv"):
            raw_items = list(csv.DictReader(io.StringIO(text)))
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Поддерживаются только файлы .json и .csv",
            )
        items = input_list_adapter.validate_python(raw_items)
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Файл должен быть в UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Некорректный JSON") from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail="Каждая запись должна содержать поля id и raw_address",
        ) from exc

    results = await _parse_many(items, session)
    await session.commit()
    return results


@router.get(
    "/records",
    response_model=list[AddressResult],
    summary="Получить сохранённые адреса",
    description="Возвращает последние результаты обработки из PostgreSQL.",
)
async def list_records(
    limit: int = Query(default=500, ge=1, le=2_000),
    session: AsyncSession = Depends(get_session),
) -> list[AddressResult]:
    return await ChallengeRecordService(session).list_recent(limit=limit)


@router.patch(
    "/records/{record_id}",
    response_model=AddressResult,
    summary="Сохранить ручное исправление",
)
async def correct_record(
    record_id: uuid.UUID,
    correction: AddressCorrection,
    session: AsyncSession = Depends(get_session),
) -> AddressResult:
    result = await ChallengeRecordService(session).correct(record_id, correction)
    if result is None:
        raise HTTPException(status_code=404, detail="Сохранённый адрес не найден")
    await session.commit()
    return result
