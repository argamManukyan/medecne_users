import pytest
from sqlalchemy.exc import IntegrityError
from src.exceptions.base_exceptions import ObjectDoesNotExists
from src.services import user_group_service
from tests.conftest import async_session_maker


@pytest.mark.asyncio
async def test_get_all_user_group(user_group_factory):
    await user_group_factory.create_batch()
    async with user_group_factory._meta.sqlalchemy_session as session:
        all_groups = await user_group_service.get_all_groups(session=session)
        assert len(all_groups) == 4


@pytest.mark.parametrize(
    "object_id, result", [(1, user_group_service.model), (17, ObjectDoesNotExists)]
)
async def test_get_user_group(object_id, result):
    async with async_session_maker() as session:
        try:
            res = await user_group_service.get_group(session=session, id=object_id)
            assert res.title == "Supplier"
            assert isinstance(res, result)
        except Exception as e:
            assert e.detail == result().detail


@pytest.mark.parametrize(
    "title, objid, result",
    [
        ("Some group", 6, "Some group"),
        ("Some group", 7, IntegrityError),
    ],
)
async def test_create_user_group(title, objid, result):
    async with async_session_maker() as session:
        await session.flush()
        try:
            res = await user_group_service.create(
                session=session, data={"title": title, "id": objid}
            )
            assert res.title == result
        except Exception as e:
            assert isinstance(e, result)
