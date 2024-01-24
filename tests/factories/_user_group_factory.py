import json
from src.core.configs import BASE_DIR
from src.models.user import UserGroup
from tests.factories.base_async_factory import BaseFactory


class UserGroupFactory(BaseFactory):
    class Meta:
        model = UserGroup
        abstract = False

    @classmethod
    async def _create(cls, model_class, *args, **kwargs):
        if kwargs:
            instance = model_class(**kwargs)
            async with cls._meta.sqlalchemy_session as session:
                session.add(instance)
                await session.commit()
                await session.close()
            return instance

    @classmethod
    async def create_batch(cls, size=None, **kwargs):
        fix_path = BASE_DIR / "src" / "fixtures" / "usergroup.json"
        with open(fix_path) as file:
            data = json.load(file)
            for item in data:
                await cls._create(model_class=cls._meta.model, **item)
