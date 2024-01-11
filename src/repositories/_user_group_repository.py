from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from src.models import UserGroup
from src.repositories.initial import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UserGroupRepository(BaseRepository):
    model = UserGroup

    @classmethod
    async def check_group(cls, session: AsyncSession, filter_kwargs: dict) -> bool:
        """Returns a boolean expression if user group(s) are existing"""
        print(session)
        stmt = await session.scalars(select(cls.model).filter_by(**filter_kwargs))

        return bool(stmt.all())

    # @classmethod
    # async def crate_bulk(cls, session: AsyncSession, obj_list: Iterable):
    #     """Creates a bunch of instances"""
    #
    #     group_list = [cls.model(**data) for data in obj_list]
    #     session.add_all(group_list)
    #     await session.commit()

    @classmethod
    async def create(cls, session: AsyncSession, data: dict) -> model:
        instance = cls.model(**data)
        session.add(instance)
        await session.commit()
        return instance
