import asyncio
import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src import messages
from src.core.constants import TokenTypes
from src.models import User
from src.exceptions.auth_exceptions import (
    EmailDuplication,
    UserDoesNotFound,
    InvalidOTP,
    InvalidData,
    UnAuthorized,
    UnActivated,
    AccountDeleted,
    AccountAlreadyVerified,
    PasswordsDidNotMatch,
    PermissionDenied,
)
from src.schemas.auth import (
    AccountVerificationScheme,
    LoginSchema,
    TokenResponseScheme,
    ResetPasswordConfirmScheme,
    SetNewPasswordScheme,
    RefreshTokenScheme,
)
from src.schemas.base import BaseMessageResponse
from src.schemas.user import UserCreateSchema
from src.utils.auth_helpers import (
    hash_password,
    validate_password,
    generate_otp_code,
    decode_jwt,
    decode_user_id,
    check_token_validity, tokenize,
)


class UserServie:
    """User service group"""

    model = User

    @classmethod
    async def get_user(cls, session: AsyncSession, **kwargs) -> Optional[User]:
        """Returns a user instance"""

        stmt = select(cls.model).filter_by(**kwargs)

        result = await session.scalars(stmt)

        return result.one_or_none()

    @classmethod
    async def create_user(
        cls, data: UserCreateSchema, session: AsyncSession
    ) -> BaseMessageResponse:
        """Returns new user object"""
        await asyncio.sleep(1)  # For avoiding repetition of otp_code's

        user_data = data.model_dump().copy()
        password = user_data.pop("password")
        user_data["password"] = hash_password(password)
        user_data["otp_code"] = generate_otp_code()
        user_data["attempts_count"] = 3
        try:
            stmt = cls.model(**user_data)
            session.add(stmt)
            # TODO:Send email
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            raise EmailDuplication
        except ValueError as e:
            await session.rollback()
            raise InvalidData(f"{e}")

        return BaseMessageResponse(message=messages.USER_CREATED_SUCCESSFULLY)

    @classmethod
    async def verify_account(
        cls, data: AccountVerificationScheme, session: AsyncSession
    ) -> BaseMessageResponse:
        """Verifies user account and reruns neither success message nor any exception"""

        user = await cls.get_user(session=session, email=data.email)
        if not user:
            raise UserDoesNotFound

        if user.is_active:
            raise AccountAlreadyVerified

        if user.otp_code != data.otp_code:
            user.attempts_count -= 1
            if user.attempts_count == 0:
                await session.delete(user)
                await session.commit()
                raise AccountDeleted
            await session.commit()
            raise InvalidOTP(attempts_num=user.attempts_count)

        user.attempts_count = 3
        user.otp_code = None
        user.is_active = True
        await session.commit()

        return BaseMessageResponse(message=messages.ACCOUNT_VERIFIED)

    @classmethod
    async def login(
        cls, login_data: LoginSchema, session: AsyncSession
    ) -> TokenResponseScheme:
        """Returns a couple of access and refresh tokens"""

        user = await cls.get_user(session=session, email=login_data.email)

        if not user:
            raise UserDoesNotFound

        if not user.is_active:
            raise UnActivated

        if not validate_password(login_data.password, user.password):
            raise UnAuthorized

        user.last_login = datetime.datetime.now()
        token_data = await tokenize(session=session, user_id=user.id)
        await session.commit()
        return token_data

    @classmethod
    async def refresh_token(
        cls, payload: RefreshTokenScheme, session: AsyncSession
    ) -> TokenResponseScheme:
        """Returns new refresh and access tokens"""
        token_data = decode_jwt(payload.refresh_token)

        if token_data["token_type"] != TokenTypes.REFRESH.value:
            raise UnAuthorized

        check_token = await check_token_validity(
            session=session, refresh_token=payload.refresh_token, expired=False
        )

        if not check_token:
            raise UnAuthorized

        check_token.expired = True

        user_id: int = decode_user_id(token_data["sub"])
        token_data = await tokenize(session=session, user_id=user_id)
        await session.commit()
        return token_data

    @classmethod
    async def logout(
        cls,
        session: AsyncSession,
        token: str,
    ) -> BaseMessageResponse:
        result = await check_token_validity(
            session=session, access_token=token, expired=False
        )

        if not result:
            raise UnAuthorized

        result.expired = True
        await session.commit()

        return BaseMessageResponse(message=messages.LOGOUT)

    @classmethod
    async def request_otp(
        cls, payload: LoginSchema, session: AsyncSession
    ) -> BaseMessageResponse:
        """Resets a new OTP code for the user"""
        user = await cls.get_user(session=session, email=payload.email)

        if not user:
            raise UserDoesNotFound

        if not validate_password(
            password=payload.password, hashed_password=user.password
        ):
            raise UnAuthorized

        if user.is_active:
            raise AccountAlreadyVerified

        user.otp_code = generate_otp_code()
        user.attempts_count -= 1
        if user.attempts_count == 0:
            await session.delete(user)
            await session.commit()
            raise AccountDeleted
        await session.commit()

        return BaseMessageResponse(message=messages.OTP_RESENT)

    @classmethod
    async def reset_password(
        cls, email: str, session: AsyncSession
    ) -> BaseMessageResponse:
        """Resets a new password for the user"""

        user = await cls.get_user(email=email, session=session)

        user.otp_code = generate_otp_code()
        # TODO:Sending new OTP code by email

        await session.commit()

        return BaseMessageResponse(message=messages.PASSWORD_RESET_MESSAGE)

    @classmethod
    async def reset_password_confirm(
        cls, payload: ResetPasswordConfirmScheme, session: AsyncSession
    ) -> BaseMessageResponse:
        """Sets a new password after reset process"""

        if payload.new_password != payload.re_new_password:
            raise PasswordsDidNotMatch

        user = await cls.get_user(
            email=payload.email, otp_code=payload.otp_code, session=session
        )

        if not user:
            raise UserDoesNotFound

        user.otp_code = None
        user.password = hash_password(payload.new_password)
        await session.commit()

        return BaseMessageResponse(message=messages.PASSWORD_CHANGED_MESSAGE)

    @classmethod
    async def set_new_password(
        cls, payload: SetNewPasswordScheme, session: AsyncSession, user_id: int
    ) -> BaseMessageResponse:
        """Sets a new password for a user"""

        if payload.new_password != payload.re_new_password:
            raise PasswordsDidNotMatch

        user = await cls.get_user(session=session, id=user_id)

        if not user:
            raise UserDoesNotFound

        if not validate_password(payload.old_password, user.password):
            raise PermissionDenied

        user.password = hash_password(payload.new_password)
        await session.commit()

        return BaseMessageResponse(message=messages.PASSWORD_CHANGED_MESSAGE)
