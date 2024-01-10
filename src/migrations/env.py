import asyncio
import itertools
import json
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool, select
from src.core.configs import settings, BASE_DIR
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.constants import MAIN_OPERATIONS, JsonType, ALLOW_ACTION, DENY_ACTION
from src.core.database import BaseModel, async_session
from alembic import context
from src.models import *
from src.repositories import user_group_repository

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = BaseModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

config.set_main_option("sqlalchemy.url", settings.db.db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def _policies_generator(tables: list, policies: JsonType, group_id: int) -> JsonType:
    """Builds and returns json of permission policies"""
    key_list = []

    action_combinations = itertools.product(tables, MAIN_OPERATIONS)

    for action in action_combinations:
        key_list.append("_".join(action))

    polices = json.loads(policies)
    for action_key in key_list:
        if not polices.get(action_key):
            polices[action_key] = ALLOW_ACTION if group_id == 4 else DENY_ACTION

    return json.dumps(polices)


async def set_user_groups() -> None:
    fixture_source = BASE_DIR / "src" / "fixtures" / "usergroup.json"
    with open(fixture_source) as groups_source:
        user_groups = json.load(groups_source)
        async with async_session() as session:
            for group in user_groups:
                if not await user_group_repository.check_group(
                    session=session, filter_kwargs={"id": group["id"]}
                ):
                    await user_group_repository.create(session=session, data=group)
                await create_permissions(user_group_id=group["id"])


async def create_permissions(user_group_id: int) -> None:
    """After migration will be created permissions depended on the user_group"""

    async with async_session() as session:
        stmt = select(Permission).filter_by(user_group_id=user_group_id)
        res = await session.scalars(stmt)
        result = res.one_or_none()
        if not result:
            obj = Permission(user_group_id=user_group_id, policies=json.dumps({}))
            session.add(obj)
            await session.commit()


async def set_permission_policies():
    tables = list(
        filter(lambda x: x != Permission.__tablename__, list(target_metadata.tables))
    )
    stmt = select(Permission).join(UserGroup)
    async with async_session() as session:
        scalars = await session.scalars(stmt)

        results = scalars.all()

        for result in results:
            result.policies = _policies_generator(
                tables, result.policies, result.user_group_id
            )

            await session.commit()
            await session.refresh(result)


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = context.config.attributes.get("connection", None)
    if connectable is None:
        connectable = AsyncEngine(
            engine_from_config(
                config.get_section(config.config_ini_section),
                prefix="sqlalchemy.",
                poolclass=pool.NullPool,
                future=True,
            )
        )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


async def main() -> None:
    await asyncio.gather(
        run_migrations_online(),
        set_user_groups(),
    )
    await asyncio.ensure_future(set_permission_policies())


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(main())
