import json
from typing import Iterable

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.configs import BASE_DIR
from sqlalchemy import select

from src.core.database import get_session
from src.models import UserGroup


class UserGroupRepository:
    model = UserGroup

    @classmethod
    async def initial_user_groups(cls, session: AsyncSession = Depends(get_session)):
        if not await cls.check_groups(session):
            fixture_source = BASE_DIR / "src" / "fixtures" / "usergroup.json"
            with open(fixture_source) as groups_source:
                user_groups = json.load(groups_source)
                await cls.crate_bulk(session=session, obj_list=user_groups)

    @classmethod
    async def check_groups(cls, session) -> bool:
        """Returns boolean an expression if user groups are existing"""
        stmt = await session.scalars(select(cls.model))

        return bool(stmt.all())

    @classmethod
    async def crate_bulk(cls, session: AsyncSession, obj_list: Iterable):
        """Creates a bunch of instances"""

        group_list = [cls.model(**data) for data in obj_list]
        session.add_all(group_list)
        await session.commit()
