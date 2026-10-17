from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.parser.challenge import parse_address_safely
from app.reference.jana_repository import JanaReferenceRepository
from app.schemas.challenge import AddressInput, AddressResult
from app.storage.database import get_session


router = APIRouter()
input_list_adapter = TypeAdapter(list[AddressInput])


async def _parse_many(
    items: list[AddressInput], repository: JanaReferenceRepository
) -> list[AddressResult]:
    settings = get_settings()
    if len(items) > settings.max_batch_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Максимум записей в одном запросе: {settings.max_batch_size}",
        )
    results: list[AddressResult] = []
    for item in items:
        parsed = parse_address_safely(item)
        results.append(await repository.enrich(parsed))
    return results


@router.post(
    "/parse",
    response_model=AddressResult,
    summary="Разобрать один адрес",
    description=(
        "Принимает `id` и исходный адрес. Возвращает плоскую структуру из задания "
        "и уточняет результат по справочнику PostgreSQL."
    ),
)
async def parse_one(
    payload: AddressInput,
    session: AsyncSession = Depends(get_session),
) -> AddressResult:
    repository = JanaReferenceRepository(session)
    return await repository.enrich(parse_address_safely(payload))


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
    return await _parse_many(payload, JanaReferenceRepository(session))


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

    return await _parse_many(items, JanaReferenceRepository(session))
