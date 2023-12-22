import pytest_asyncio
from src.models import User
from src.services import user_service
from src.schemas import UserCreateSchema
from tests.conftest import async_session_maker


@pytest_asyncio.fixture(scope="function")
async def user_fixture() -> User:
    async with async_session_maker() as session:
        user_schema = UserCreateSchema(
            first_name="Test",
            last_name="User",
            email="test@mail.ru",
            password="Senior1234!",
        )
        await user_service.create_user(user_schema, session=session)
        stmt = await user_service.get_user(email=user_schema.email, session=session)

        return stmt
