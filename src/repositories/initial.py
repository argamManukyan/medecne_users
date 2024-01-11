from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import select, inspect, update
from sqlalchemy.orm import RelationshipProperty, RelationshipDirection

from src.exceptions.base_exceptions import ObjectDoesNotExists
from src.schemas.base import GenericSchema

if TYPE_CHECKING:
    from src.core.constants import DbBaseModel
    from pydantic import BaseModel as PydanticBase
    from typing import Iterable, Callable
    from src.core.database import BaseModel
    from sqlalchemy.ext.asyncio import AsyncSession


ISONETOONE: Callable[[RelationshipProperty], bool] = (
    lambda related_column: related_column.direction == RelationshipDirection.ONETOMANY
    and related_column.uselist is False
)


class BaseRepository:
    """Base repository class, here is implemented for the general purpose created logics."""

    @classmethod
    async def delete_related_objects(
        cls,
        table_name: str,
        parent_id: int,
        parent_model: BaseModel,
        session: AsyncSession,
    ):
        """Deletes all related objects."""

        stmt = select(table_name).join(parent_model).where(parent_model.id == parent_id)
        result = await session.scalars(stmt)
        deleting_data = result.unique().all()

        for del_data in deleting_data:
            await session.delete(del_data)

    @classmethod
    async def get_object_existence(
        cls, session: AsyncSession, model: DbBaseModel, **filter_kwargs
    ):
        """Checking object existing depended on filter kwargs"""

        stmt = select(model).filter_by(**filter_kwargs)

        result = await session.scalars(stmt)
        result = result.one_or_none()

        if not result:
            raise ObjectDoesNotExists

    @classmethod
    def _preparing_base_fields(
        cls, columns: Iterable, payload: PydanticBase | dict
    ) -> dict:
        """Returns a dict based on base fields (no Fk)"""
        if not isinstance(payload, dict):
            payload = payload.model_dump()

        return {key: value for key, value in payload.items() if key in columns}

    @classmethod
    def preparing_base_fields(cls, columns: Iterable, payload: PydanticBase | dict):
        """Public method to deal with protected method `_preparing_base_fields`"""
        return cls._preparing_base_fields(columns, payload)

    @classmethod
    def _get_related_and_base_columns(
        cls,
        inspect_table,
    ) -> tuple[list[RelationshipProperty], Iterable]:
        """Returns foreign keys and local columns"""
        related_columns = list(inspect_table.relationships)
        basic_columns = inspect_table.columns
        return related_columns, basic_columns

    @classmethod
    def get_related_and_base_columns(cls, inspect_table):
        """Public method to deal with protected method `_get_related_and_base_columns`"""
        return cls._get_related_and_base_columns(inspect_table)

    @classmethod
    async def _update_existing_data(
        cls, session: AsyncSession, base_data: dict, model: DbBaseModel, **kwargs
    ) -> DbBaseModel:
        """Updating models and returning the current model instance"""

        stmt = update(model).filter_by(**kwargs).values(**base_data).returning(model)
        await session.execute(stmt)
        element_stmt = select(model).filter_by(**kwargs)
        result = await session.scalars(element_stmt)
        selected_item = result.one_or_none()
        await session.refresh(selected_item)
        return selected_item

    @classmethod
    async def update_existing_data(
        cls,
        *,
        session: AsyncSession,
        base_data: dict,
        model: DbBaseModel,
        filter_kwargs: dict,
    ):
        """Update existing data public method , this calls a protected method, jost encapsulates method for update"""

        return cls._update_existing_data(session, base_data, model, **filter_kwargs)

    @classmethod
    async def create_or_update_instance_with_base_fields(
        cls,
        session: AsyncSession,
        prepared_base_data: dict,
        model: DbBaseModel,
        parent_backref: str,
        parent_id: int,
    ) -> DbBaseModel:
        """Handler for creating or updating the existing instances"""

        if "id" in prepared_base_data:
            filter_data = dict(id=prepared_base_data["id"])
            await cls.get_object_existence(session=session, model=model, **filter_data)
            parent_runtime = await cls._update_existing_data(
                session=session,
                base_data=prepared_base_data,
                id=prepared_base_data["id"],
                model=model,
            )
        else:
            parent_setter_mapping = {f"{parent_backref}_id": parent_id}
            parent_runtime = model(**parent_setter_mapping, **prepared_base_data)
            session.add(parent_runtime)
            await session.commit()

        return parent_runtime

    @classmethod
    async def combine_relations(
        cls,
        *,
        session: AsyncSession,
        callable_func: Callable,
        inner_relations: Iterable[RelationshipProperty],
        payload: dict,
        parent_runtime: DbBaseModel,
    ):
        """Combines and deals with relations"""

        for related_column in inner_relations:
            if (
                related_column.direction == RelationshipDirection.ONETOMANY
                and related_column.key in payload
            ):
                await callable_func(
                    related_column.mapper.entity,
                    GenericSchema(data=payload.get(related_column.key)),
                    session=session,
                    parent_id=parent_runtime.id,
                    parent_backref=related_column.back_populates,
                )
            elif all(
                [
                    ISONETOONE(related_column),
                    related_column.key in payload,
                ]
            ):
                await callable_func(
                    related_column.mapper.entity,
                    GenericSchema(data=payload.get(related_column.key)),
                    session=session,
                    parent_id=parent_runtime.id,
                    parent_backref=related_column.back_populates,
                )
            # elif related_column.direction.MANYTOONE:
            # elif related_column.direction.MANYTOONE:

    @classmethod
    async def routine_creation_or_update_instances(
        cls,
        *,
        session: AsyncSession,
        base_columns: Iterable,
        payload: dict,
        model: DbBaseModel,
        inner_relations: Iterable,
        parent_id: int | None = None,
        parent_backref: str | None = None,
    ):
        """Will be created or updated `model` instance depending on their existence"""

        prepared_base_data = cls._preparing_base_fields(
            base_columns, GenericSchema(data=payload)
        )
        parent_runtime = await cls.create_or_update_instance_with_base_fields(
            session=session,
            prepared_base_data=prepared_base_data,
            model=model,
            parent_backref=parent_backref,
            parent_id=parent_id,
        )

        await cls.combine_relations(
            session=session,
            callable_func=cls.find_relations,
            inner_relations=inner_relations,
            payload=payload,
            parent_runtime=parent_runtime,
        )

    @classmethod
    async def find_relations(
        cls,
        model,
        payload: BaseModel | GenericSchema,
        session: AsyncSession,
        parent_id=None,
        parent_backref=None,
    ):
        """
        Finds the relations and recursively creates or updates existing instances.
        """

        inspect_table = inspect(model)
        payload = payload.model_dump(exclude_unset=True, exclude_none=True)

        inner_relations, base_columns = cls._get_related_and_base_columns(inspect_table)
        if isinstance(payload, list):
            for p_item in payload:
                await cls.routine_creation_or_update_instances(
                    session=session,
                    base_columns=base_columns,
                    payload=p_item,
                    model=model,
                    inner_relations=inner_relations,
                    parent_id=parent_id,
                    parent_backref=parent_backref,
                )

        else:
            await cls.routine_creation_or_update_instances(
                session=session,
                base_columns=base_columns,
                payload=payload,
                model=model,
                inner_relations=inner_relations,
                parent_id=parent_id,
                parent_backref=parent_backref,
            )
