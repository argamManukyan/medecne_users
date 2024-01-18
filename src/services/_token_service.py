from __future__ import annotations
from typing import TYPE_CHECKING

from src.repositories import token_repository
from src.schemas.auth import TokenResponseScheme, RefreshTokenScheme
from src.utils.auth_helpers import create_refresh_and_access_tokens, decode_user_id

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class TokenService:
    model = token_repository.model
    repository = token_repository

    @classmethod
    async def check_token_validity(cls, session: AsyncSession, **kwargs) -> model:
        """Returns a model instance if it is valid"""
        return await cls.repository.check_token_validity(session=session, **kwargs)

    @classmethod
    async def update_token(cls, session: AsyncSession, token_id: int, **kwargs) -> None:
        """Updates the token state"""

        await cls.repository.update_token(session=session, token_id=token_id, **kwargs)

    @classmethod
    async def tokenize(cls, session: AsyncSession, user_id: int) -> TokenResponseScheme:
        """Creates refresh and access tokens for the particular user"""

        token_data = create_refresh_and_access_tokens(user_id=user_id)
        return await cls.repository.tokenize(session=session, token_schema=token_data)

    @classmethod
    async def refresh_token(
        cls, session: AsyncSession, payload: RefreshTokenScheme, token_data: dict
    ) -> TokenResponseScheme:
        """Refreshes and returns a couple of refresh and access tokens"""

        token = await cls.check_token_validity(
            session=session, refresh_token=payload.refresh_token, expired=False
        )
        await cls.update_token(session=session, expired=True, token_id=token.id)
        user_id: int = decode_user_id(token_data["sub"])
        token_data = await cls.tokenize(session=session, user_id=user_id)
        return token_data
