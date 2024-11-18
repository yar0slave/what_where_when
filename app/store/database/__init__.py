
from typing import TYPE_CHECKING, Any
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy.ext.asyncio import create_async_engine

from app.store.database.sqlalchemy_base import BaseModel

if TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self, app: "Application") -> None:
        self.app = app

        self.engine: AsyncEngine | None = None
        self._db: type[DeclarativeBase] = BaseModel
        self.session: async_sessionmaker[AsyncSession] | None = None

    async def connect(self, *args: Any, **kwargs: Any) -> None:
        user = self.app.config.database.user
        password = self.app.config.database.password
        host = self.app.config.database.host
        database = self.app.config.database.database
        port = self.app.config.database.port

        self.engine = create_async_engine(
            URL.create(
                drivername="postgresql+asyncpg",
                username=user,
                password=password,
                host=host,
                port=port,
                database=database
            ),
        )

        self.session = async_sessionmaker(
            self.engine,
            expire_on_commit=False
        )

    async def disconnect(self, *args: Any, **kwargs: Any) -> None:
        await self.session().close()