from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from src.exceptions.base_exceptions import ObjectDoesNotExists
from src.models import UserGroup
from src.repositories.initial import BaseRepository

if TYPE_CHECKING:
    from typing import Sequence, Any
    from sqlalchemy.ext.asyncio import AsyncSession


class UserGroupRepository(BaseRepository):
    model = UserGroup

    @classmethod
    async def check_group(cls, session: AsyncSession, filter_kwargs: dict) -> bool:
        """Returns a boolean expression if user group(s) are existing"""
        stmt = await session.scalars(select(cls.model).filter_by(**filter_kwargs))

        return bool(stmt.all())

    @classmethod
    async def create(cls, session: AsyncSession, data: dict) -> model:
        """Creates and returns an instance of UserGroup"""
        instance = cls.model(**data)
        session.add(instance)
        await session.commit()
        return instance

    @classmethod
    async def get_all_groups(cls, session: AsyncSession) -> Sequence[model]:
        """Returns a sequence of UserGroup's"""
        stmt = await session.scalars(select(cls.model))
        return stmt.all()

    @classmethod
    async def get_group(
        cls, session: AsyncSession, **filter_kwargs: dict[str, Any]
    ) -> model:
        """Returns an object of UserGroup"""
        stmt = select(cls.model).filter_by(**filter_kwargs)
        res = await session.scalars(stmt)
        obj = res.one_or_none()

        if not obj:
            raise ObjectDoesNotExists
        return obj
