from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory

from tests.init_db import async_session_maker


class BaseFactory(AsyncSQLAlchemyFactory):
    class Meta:
        abstract = True
        model = None
        sqlalchemy_session = async_session_maker()
