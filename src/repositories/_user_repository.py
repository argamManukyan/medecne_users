import os.path
import time

from fastapi import UploadFile
from sqlalchemy import select, update, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.core.configs import BASE_DIR, settings
from src.exceptions.auth_exceptions import (
    UserDoesNotFound,
    EmailDuplication,
    InvalidData,
    AccountAlreadyVerified,
    AccountDeleted,
    InvalidOTP,
)
from src.models import User, UserRelatedFeatures, UserRelatedFeatureValue, UserGroup
from src.schemas.auth import AccountVerificationScheme
from src.schemas.user import UserUpdateSchema
from src.utils.auth_helpers import generate_otp_code


class UserRepository:
    model = User

    @classmethod
    async def get_user(cls, session: AsyncSession, **kwargs) -> User:
        """Returns a user instance"""
        stmt = select(cls.model).options(
            joinedload(cls.model.group),
            selectinload(cls.model.features),
        )

        result = await session.scalars(stmt)
        user_object = result.one_or_none()
        if not user_object:
            raise UserDoesNotFound

        return user_object

    @classmethod
    async def create_user(cls, session: AsyncSession, user_data: dict):
        """Creates a new user"""
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

    @classmethod
    async def verify_account(
        cls, session: AsyncSession, data: AccountVerificationScheme
    ):
        """
        Verifies user account, in case of wrong otp will be risen exception.
        if wrong attempts gets up to max_attempts count account will be deleted.
        """

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

    @classmethod
    async def update_data(cls, user_id: int, session: AsyncSession, data: dict):
        stmt = (
            update(cls.model)
            .filter_by(id=user_id)
            .values(**data)
            .returning(cls.model)
            .options(selectinload(cls.model.features))
        )
        user = await session.scalars(stmt)
        return user.unique().one()

    @classmethod
    async def request_otp(cls, session: AsyncSession, user: User):
        user.otp_code = generate_otp_code()
        user.attempts_count -= 1
        if user.attempts_count == 0:
            await session.delete(user)
            await session.commit()
            raise AccountDeleted
        await session.commit()

    @classmethod
    async def update_profile_photo(
        cls, session: AsyncSession, user: User, file_path: str | None = None
    ):
        user.photo = file_path
        await session.commit()
