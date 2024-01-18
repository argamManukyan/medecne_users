from factory import LazyAttribute

from tests.factories.base_async_factory import BaseFactory
from faker import Factory as FakerFactory
from src.models import User

faker = FakerFactory.create()


class UserFactory(BaseFactory):
    class Meta:
        model = User
        abstract = False
