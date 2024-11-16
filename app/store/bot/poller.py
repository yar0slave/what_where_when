import asyncio
from asyncio import Task
from typing import Optional

from clients.tg import TgClient


class Poller:
    def __init__(self, token: str, queue: asyncio.Queue):
        self.tg_client = TgClient(token)
        self.queue = queue
        self._task: Optional[Task] = None

    async def _worker(self):
        offset = 0
        try:
            while True:
                res = await self.tg_client.get_updates_in_objects(offset=offset, timeout=60)
                for u in res.result:
                    offset = u.update_id + 1
                    try:
                        asyncio.get_running_loop()
                    except RuntimeError:
                        print("Цикл событий закрыт, завершение poller.")
                        return
                    self.queue.put_nowait(u)
        except asyncio.CancelledError:
            print("Poller worker was cancelled.")
            raise

    async def start(self):
        self._task = asyncio.create_task(self._worker())

    async def stop(self):
        if self._task:
            self._task.cancel()
            await self._task
            self._task = None
