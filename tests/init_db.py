from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.core.configs import settings
from src.core.database import BaseModel

engine_test = create_async_engine(settings.db.db_test_url, poolclass=NullPool)
async_session_maker = async_sessionmaker(
    engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

BaseModel.metadata.bind = engine_test
