import asyncio
import datetime

from fastapi import UploadFile
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio.session import AsyncSession
from src import messages
from src.core.configs import settings
from src.core.constants import TokenTypes
from src.models import User
from src.exceptions.auth_exceptions import (
    UnAuthorized,
    UnActivated,
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
from src.schemas.user import UserCreateSchema, UserUpdateSchema
from src.utils.auth_helpers import (
    hash_password,
    validate_password,
    generate_otp_code,
    decode_jwt,
)
from src.repositories import user_repository, token_repository, user_group_repository
from src.utils.base_helpers import (
    get_related_and_base_columns,
    preparing_base_fields,
    get_file_path,
    generate_filename,
)


class UserServie:
    """User service group"""

    model = User

    @classmethod
    async def get_user(cls, session: AsyncSession, **kwargs) -> User:
        """Returns a user instance"""
        return await user_repository.get_user(session=session, **kwargs)

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
        await user_group_repository.initial_user_groups(session=session)
        await user_repository.create_user(session=session, user_data=user_data)
        return BaseMessageResponse(message=messages.USER_CREATED_SUCCESSFULLY)

    @classmethod
    async def verify_account(
        cls, data: AccountVerificationScheme, session: AsyncSession
    ) -> BaseMessageResponse:
        """Verifies user account and reruns neither success message nor any exception"""

        await user_repository.verify_account(session=session, data=data)
        return BaseMessageResponse(message=messages.ACCOUNT_VERIFIED)

    @classmethod
    async def login(
        cls, login_data: LoginSchema, session: AsyncSession
    ) -> TokenResponseScheme:
        """Returns a couple of access and refresh tokens"""

        user = await user_repository.get_user(session=session, email=login_data.email)

        if not user.is_active:
            raise UnActivated

        if not validate_password(login_data.password, user.password):
            raise UnAuthorized

        await user_repository.update_data(
            session=session,
            data=dict(last_login=datetime.datetime.now()),
            user_id=user.id,
        )
        token_data = await token_repository.tokenize(session=session, user_id=user.id)
        return token_data

    @classmethod
    async def refresh_token(
        cls, payload: RefreshTokenScheme, session: AsyncSession
    ) -> TokenResponseScheme:
        """Returns new refresh and access tokens"""
        token_data = decode_jwt(payload.refresh_token)

        if token_data["token_type"] != TokenTypes.REFRESH.value:
            raise UnAuthorized

        return await token_repository.refresh_token(
            session=session, token_data=token_data, payload=payload
        )

    @classmethod
    async def logout(
        cls,
        session: AsyncSession,
        token: str,
    ) -> BaseMessageResponse:
        """Logs out of the user and marks tokens expired"""

        token = await token_repository.check_token_validity(
            session=session, access_token=token, expired=False
        )
        await token_repository.update_token(
            session=session, expired=True, token_id=token.id
        )

        return BaseMessageResponse(message=messages.LOGOUT)

    @classmethod
    async def request_otp(
        cls, payload: LoginSchema, session: AsyncSession
    ) -> BaseMessageResponse:
        """Resets a new OTP code for the user"""
        user = await user_repository.get_user(session=session, email=payload.email)

        if not validate_password(
            password=payload.password, hashed_password=user.password
        ):
            raise UnAuthorized
        if user.is_active:
            raise AccountAlreadyVerified

        await user_repository.request_otp(session=session, user=user)
        return BaseMessageResponse(message=messages.OTP_RESENT)

    @classmethod
    async def reset_password(
        cls, email: str, session: AsyncSession
    ) -> BaseMessageResponse:
        """Resets a new password for the user"""

        user = await user_repository.get_user(email=email, session=session)

        await user_repository.update_data(
            session=session, data=dict(otp_code=generate_otp_code()), user_id=user.id
        )

        # TODO:Sending new OTP code by email

        return BaseMessageResponse(message=messages.PASSWORD_RESET_MESSAGE)

    @classmethod
    async def reset_password_confirm(
        cls, payload: ResetPasswordConfirmScheme, session: AsyncSession
    ) -> BaseMessageResponse:
        """Sets a new password after reset process"""

        if payload.new_password != payload.re_new_password:
            raise PasswordsDidNotMatch

        user = await user_repository.get_user(
            email=payload.email, otp_code=payload.otp_code, session=session
        )

        await user_repository.update_data(
            session=session,
            user_id=user.id,
            data=dict(otp_code=None, password=hash_password(payload.new_password)),
        )

        return BaseMessageResponse(message=messages.PASSWORD_CHANGED_MESSAGE)

    @classmethod
    async def set_new_password(
        cls, payload: SetNewPasswordScheme, session: AsyncSession, user_id: int
    ) -> BaseMessageResponse:
        """Sets a new password for a user"""

        if payload.new_password != payload.re_new_password:
            raise PasswordsDidNotMatch

        user = await user_repository.get_user(session=session, id=user_id)

        if not validate_password(payload.old_password, user.password):
            raise PermissionDenied

        user.password = hash_password(payload.new_password)

        await user_repository.update_data(
            session=session,
            user_id=user.id,
            data=dict(password=hash_password(payload.new_password)),
        )

        return BaseMessageResponse(message=messages.PASSWORD_CHANGED_MESSAGE)

    @classmethod
    async def patch_user(
        cls,
        session: AsyncSession,
        user_id: int,
        payload: UserUpdateSchema | None = None,
    ):
        inspect_table = inspect(cls.model)

        related_columns, base_columns = get_related_and_base_columns(inspect_table)

        base_data_dict = preparing_base_fields(base_columns, payload)

        # TODO: saving related column data

        return await user_repository.update_data(
            session=session, user_id=user_id, data=base_data_dict
        )

    @classmethod
    async def update_profile_photo(
        cls, session: AsyncSession, user_id: int, file: UploadFile | None = None
    ):
        user = await cls.get_user(session=session, id=user_id)

        filename = generate_filename(file_prefix=user.full_name)
        file_path = get_file_path(
            settings.file.users_file_direction,
            filename=filename,
            file=file,
            old_path=user.photo,
        )

        await user_repository.update_profile_photo(
            session=session, user=user, file_path=file_path
        )
