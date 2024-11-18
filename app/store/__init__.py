import asyncio
import os
import typing

from app.store.database.sqlalchemy_base import BaseModel

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.bot.base import Bot

        self.app = app
        self.bots_manager = Bot(app.config.bot.token, n=2)


def setup_store(app: "Application"):
    app.store = Store(app)

    async def on_startup(app: "Application"):
        await app.store.bots_manager.start()

    async def on_cleanup(app: "Application"):
        await app.store.bots_manager.stop()

        pending_tasks = [
            task
            for task in asyncio.all_tasks()
            if task is not asyncio.current_task()
        ]

        await asyncio.gather(*pending_tasks, return_exceptions=True)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
