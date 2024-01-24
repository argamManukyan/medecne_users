import fastapi.exceptions
import pytest

from src.exceptions.auth_exceptions import InvalidOTP, UnAuthorized
from src.schemas.auth import AccountVerificationScheme, TokenResponseScheme, LoginSchema
from src.schemas.base import BaseMessageResponse
from src.services import user_service
from src.schemas import UserCreateSchema
from tests.conftest import async_session_maker


test_user_create_schema = UserCreateSchema(
    first_name="Test", last_name="Testovich", email="test@mail.ru", password="Test1234!"
)


@pytest.mark.parametrize(
    "test_schema, result",
    (
        (test_user_create_schema, BaseMessageResponse),
        (test_user_create_schema, fastapi.exceptions.HTTPException),
    ),
)
async def test_create_user(test_schema: UserCreateSchema, result):
    async with async_session_maker() as session:
        try:
            response = await user_service.create_user(data=test_schema, session=session)
            assert isinstance(response, result)
        except Exception as e:
            assert e.__class__ is result


@pytest.mark.parametrize("email, result", [("test@mail.ru", False)])
async def test_get_user(email, result):
    async with async_session_maker() as session:
        result = await user_service.get_user(email=email, session=session)
        assert result.is_active is False
        assert result.first_name == "Test"
        assert result.last_name == "Testovich"
        result.otp_code = "12345"
        session.add(result)
        await session.commit()
        await session.refresh(result)


@pytest.mark.parametrize(
    "email,otp_code,result",
    [
        ("test@mail.ru", "34556", InvalidOTP),
        ("test@mail.ru", "34546", InvalidOTP),
        ("test@mail.ru", "12045", InvalidOTP),
        ("test@mail.ru", "12045", fastapi.HTTPException),
    ],
)
async def test_verify_user_account_fail(email, otp_code, result):
    data = AccountVerificationScheme(email=email, otp_code=otp_code)
    async with async_session_maker() as session:
        try:
            await user_service.verify_account(session=session, data=data)
        except Exception as e:
            assert e.__class__ is result


@pytest.mark.parametrize("email, result", [("test@mail.ru", BaseMessageResponse)])
async def test_verify_user_account_success(email, result):
    async with async_session_maker() as session:
        await user_service.create_user(data=test_user_create_schema, session=session)
        user = await user_service.get_user(email=email, session=session)
        assert user.is_active is False
        data = AccountVerificationScheme(email=email, otp_code=user.otp_code)
        res = await user_service.verify_account(session=session, data=data)
        await session.refresh(user)
        assert user.is_active is True
        assert res.__class__ is result


@pytest.mark.parametrize(
    "email, password, result",
    [
        ("test@mail.ru", "Test1234", fastapi.HTTPException),  # invalid password
        ("test@mail.ru", "Test1234!", fastapi.HTTPException),  # inactive user
    ],
)
async def test_login_fail(email, password, result):
    data = LoginSchema(email=email, password=password)
    async with async_session_maker() as session:
        try:
            user = await user_service.get_user(session=session, email=email)
            await user_service.login(session=session, login_data=data)
        except Exception as e:
            if e.detail == UnAuthorized.detail:
                user.is_active = False
                await session.commit()
                await session.refresh(user)
                assert e.__class__ is result

            else:
                assert e.__class__ is result
                user.is_active = True
                await session.commit()
                await session.refresh(user)


@pytest.mark.parametrize(
    "email, password, result",
    [("test@mail.ru", "Test1234!", TokenResponseScheme)],
)
async def test_login_success(email, password, result):
    data = LoginSchema(email=email, password=password)
    async with async_session_maker() as session:
        response = await user_service.login(session=session, login_data=data)
        assert response.__class__ is result
