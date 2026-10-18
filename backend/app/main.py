from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from swagger_ui_bundle import swagger_ui_path

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
    docs_url=None,
    redoc_url=None,
)

if settings.environment != "production":
    app.mount(
        "/swagger-ui",
        StaticFiles(directory=swagger_ui_path),
        name="swagger-ui",
    )

    @app.get("/docs", include_in_schema=False)
    async def swagger_ui():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{settings.app_name} — Swagger UI",
            swagger_js_url="/swagger-ui/swagger-ui-bundle.js",
            swagger_css_url="/swagger-ui/swagger-ui.css",
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
