from __future__ import annotations
from typing import TYPE_CHECKING

from src.repositories import user_group_repository

if TYPE_CHECKING:
    from typing import Sequence
    from sqlalchemy.ext.asyncio import AsyncSession


class UserGroupService:
    model = user_group_repository.model
    repository = user_group_repository

    @classmethod
    async def check_group(cls, session: AsyncSession, **filter_kwargs) -> bool:
        """Check the group existing depended on the filter_kwargs"""
        return await cls.repository.check_group(
            session=session, filter_kwargs=filter_kwargs
        )

    @classmethod
    async def create(cls, session: AsyncSession, data: dict) -> model:
        """Returns an instance of created model"""
        return await cls.repository.create(session, data)

    @classmethod
    async def get_all_groups(cls, session: AsyncSession) -> Sequence[model]:
        """Returns a sequence of model's"""
        return await cls.repository.get_all_groups(session)

    @classmethod
    async def get_group(cls, session: AsyncSession, **filter_kwargs) -> model:
        """Returns a model instance. Model existing is depended on filtered kwargs if there are kwargs"""
        return await cls.repository.get_group(session, **filter_kwargs)
