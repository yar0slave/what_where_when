import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.store.database.models import BaseModel

if TYPE_CHECKING:
    from app.web.app import Application

logger = logging.getLogger(__name__)


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
                database=database,
            ),
        )

        self.session = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )

        try:
            async with self.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                logger.info("Подключение к базе данных установлено.")
        except Exception as e:
            logger.error("Ошибка подключения к базе данных: %s", e)

    async def disconnect(self, *args: Any, **kwargs: Any) -> None:
        if self.session:
            await self.session().close()
