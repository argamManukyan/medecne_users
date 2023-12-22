import pytest
from fastapi.exceptions import HTTPException
from pydantic_core import ValidationError

from src import messages
from src.schemas import UserCreateSchema
from src.schemas.auth import AccountVerificationScheme
from src.schemas.base import BaseMessageResponse
from tests.conftest import async_session_maker
from src.services import user_service


@pytest.mark.parametrize(
    "first_name, last_name, email, password, result",
    [
        (
            "Test",
            "Testovich",
            "test12@mail.ru",
            "Test12!",
            BaseMessageResponse(message=messages.USER_CREATED_SUCCESSFULLY),
        ),
        (
            "Test",
            "Testovich",
            "test12@mail.ru",
            "Test12!",
            HTTPException,
        ),
        (
            "Test",
            "Testovich",
            "test1s2@mail.ru",
            "Testxasxsax12!",
            ValidationError,
        ),
    ],
)
async def test_service_create_process(first_name, last_name, email, password, result):
    async with async_session_maker() as session:
        try:
            user_schema = UserCreateSchema(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
            )
            res = await user_service.create_user(session=session, data=user_schema)
            assert res == result
        except Exception as e:
            assert isinstance(e.__class__, result.__class__)


@pytest.mark.asyncio
async def test_verify_account_success(user_fixture: user_service.model):
    async with async_session_maker() as session:
        payload = AccountVerificationScheme(
            otp_code=user_fixture.otp_code,
            email=user_fixture.email,
        )

        response = await user_service.verify_account(data=payload, session=session)

        assert response == BaseMessageResponse(message=messages.ACCOUNT_VERIFIED)

        await session.delete(user_fixture)
        await session.commit()
