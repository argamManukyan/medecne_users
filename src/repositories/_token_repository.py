from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import select, update

from src.exceptions.auth_exceptions import UnAuthorized
from src.models import Token
from src.utils.auth_helpers import decode_user_id, create_refresh_and_access_tokens


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.schemas.auth import RefreshTokenScheme, TokenResponseScheme


class TokenRepository:
    model = Token

    @classmethod
    async def check_token_validity(cls, session: AsyncSession, **kwargs) -> Token:
        """Returns is the token expired or no"""

        stmt = select(Token).filter_by(**kwargs)

        result = await session.scalars(stmt)

        if not (response := result.one_or_none()):
            raise UnAuthorized
        return response

    @classmethod
    async def update_token(cls, session: AsyncSession, token_id: int, **kwargs) -> None:
        """Updates the token state"""

        stmt = (
            update(cls.model)
            .where(cls.model.id == token_id)
            .values(**kwargs)
            .returning(cls.model)
        )

        await session.scalars(stmt)

    @classmethod
    async def tokenize(
        cls, session: AsyncSession, token_schema: TokenResponseScheme
    ) -> TokenResponseScheme:
        """Creates refresh and access tokens for the particular user"""

        stmt = Token(
            refresh_token=token_schema.refresh_token,
            access_token=token_schema.access_token,
        )
        session.add(stmt)
        await session.commit()
        return token_schema

    @classmethod
    async def refresh_token(
        cls, session: AsyncSession, payload: RefreshTokenScheme, token_data: dict
    ):
        """Refreshes and returns a couple of refresh and access tokens"""

        token = await cls.check_token_validity(
            session=session, refresh_token=payload.refresh_token, expired=False
        )
        await cls.update_token(session=session, expired=True, token_id=token.id)
        user_id: int = decode_user_id(token_data["sub"])

        token_data = await cls.tokenize(session=session, user_id=user_id)
        await session.commit()
        return token_data
