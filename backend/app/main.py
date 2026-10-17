from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.storage.database import engine


settings = get_settings()
OPENAPI_TAGS = [
    {
        "name": "JANA ADDRESS",
        "description": "Основной конвейер разбора одного адреса, массива или файла.",
    },
    {
        "name": "Система",
        "description": "Техническая проверка готовности backend и PostgreSQL.",
    },
]
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend хакатон-кейса **JANA ADDRESS**: извлекает из адресной строки "
        "ровно те поля, которые требуются в задании.\n\n"
        "**Главный метод для проверки: `POST /api/v1/parse/batch`.**"
    ),
    openapi_tags=OPENAPI_TAGS,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "health": f"{settings.api_v1_prefix}/health",
        "docs": "/docs",
    }
