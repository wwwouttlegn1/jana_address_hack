from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.reference.models import ReferenceType  # noqa: E402
from app.reference.repository import ReferenceRepository  # noqa: E402
from app.storage.database import async_session_factory  # noqa: E402


logger = logging.getLogger("build_reference")


def read_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.casefold() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        rows = payload.get("items") if isinstance(payload, dict) else payload
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ValueError("JSON должен содержать массив объектов")
        return rows
    if path.suffix.casefold() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))
    raise ValueError("Поддерживаются только .json и .csv")


async def import_rows(rows: list[dict[str, Any]], checkpoint_size: int) -> None:
    valid_types = {item.value for item in ReferenceType}
    async with async_session_factory() as session:
        repository = ReferenceRepository(session)
        for index, row in enumerate(rows, start=1):
            kind = str(row.get("kind", "")).strip().casefold()
            name = str(row.get("name", "")).strip()
            if kind not in valid_types or not name:
                raise ValueError(f"Строка {index}: обязательны корректные kind и name")

            parent_id = int(row["parent_id"]) if row.get("parent_id") else None
            parent_code = str(row.get("parent_code", "")).strip()
            if parent_id is None and parent_code:
                parent = await repository.get_by_code(parent_code)
                if parent is None:
                    raise ValueError(
                        f"Строка {index}: parent_code={parent_code!r} еще не загружен"
                    )
                parent_id = parent.id

            raw_attributes = row.get("attributes") or row.get("attributes_json") or {}
            attributes = (
                json.loads(raw_attributes) if isinstance(raw_attributes, str) else raw_attributes
            )
            if not isinstance(attributes, dict):
                raise ValueError(f"Строка {index}: attributes должен быть JSON-объектом")

            await repository.upsert(
                kind=kind,
                name=name,
                code=str(row.get("code", "")).strip() or None,
                parent_id=parent_id,
                attributes=attributes,
            )
            if index % checkpoint_size == 0:
                await session.commit()
                logger.info("Импортировано %s из %s", index, len(rows))
        await session.commit()
        logger.info("Готово: импортировано или обновлено %s записей", len(rows))


def main() -> None:
    parser = argparse.ArgumentParser(description="Идемпотентная загрузка адресного справочника")
    parser.add_argument("input", type=Path, help="JSON или CSV файл")
    parser.add_argument("--checkpoint-size", type=int, default=500)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    if not args.input.is_file():
        parser.error(f"Файл не найден: {args.input}")
    if args.checkpoint_size < 1:
        parser.error("--checkpoint-size должен быть больше нуля")
    asyncio.run(import_rows(read_rows(args.input), args.checkpoint_size))


if __name__ == "__main__":
    main()
