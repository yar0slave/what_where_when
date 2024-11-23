import asyncio
import typing

from app.store.bot.poller import Poller
from app.store.bot.worker import Worker

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Bot:
    def __init__(self, token: str, app: "Application"):
        self.queue = asyncio.Queue()
        self.poller = Poller(token, self.queue)
        self.worker = Worker(token, self.queue, app)

    async def start(self):
        await self.poller.start()
        await self.worker.start()

    async def stop(self):
        await self.poller.stop()
        await self.worker.stop()
