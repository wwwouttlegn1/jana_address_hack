import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient


os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["REVIEW_CONFIDENCE_THRESHOLD"] = "0.72"
os.environ["GEOCODING_ENABLED"] = "false"

from app.main import app  # noqa: E402
from app.reference.models import AddressReference  # noqa: E402, F401
from app.storage.database import Base, async_session_factory, engine  # noqa: E402
from app.storage.models import AddressRecord, BatchJob  # noqa: E402, F401


@pytest_asyncio.fixture
async def client():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as http_client:
        yield http_client
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    async with async_session_factory() as session:
        yield session
        await session.rollback()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
