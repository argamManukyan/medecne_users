from typing import AsyncGenerator

import pytest
import asyncio

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from src.core.database import get_session, BaseModel
from src.core.configs import settings
from main import app

engine_test = create_async_engine(settings.db.db_test_url, poolclass=NullPool)
async_session_maker = async_sessionmaker(
    engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

BaseModel.metadata.bind = engine_test


pytest_plugins = [
    "fixtures.fixture_user",
]


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


app.dependency_overrides[get_session] = override_get_async_session


@pytest.fixture(autouse=True, scope="session")
async def prepare_database():
    async with engine_test.begin() as conn:
        print("CREATED DATABASE")
        await conn.run_sync(BaseModel.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        print("DROPPED DATABASE")
        await conn.run_sync(BaseModel.metadata.drop_all)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    res = asyncio.new_event_loop()
    asyncio.set_event_loop(res)
    res._close = res.close
    res.close = lambda: None

    yield res

    res._close()


client = TestClient(app)


@pytest.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
