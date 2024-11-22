import asyncio
from asyncio import Task

from clients.tg import TgClient


class Poller:
    def __init__(self, token: str, queue: asyncio.Queue):
        self.tg_client = TgClient(token)
        self.queue = queue
        self._task: Task | None

    async def _worker(self):
        offset = 0
        while True:
            res = await self.tg_client.get_updates_in_objects(
                offset=offset, timeout=60
            )
            for u in res.result:
                offset = u.update_id + 1
                if u.message and u.message.chat.type in ["group", "supergroup"]:
                    try:
                        asyncio.get_running_loop()
                    except RuntimeError:
                        return
                    self.queue.put_nowait(u)

    async def start(self):
        self._task = asyncio.create_task(self._worker())

    async def stop(self):
        if self._task:
            self._task.cancel()
            await self._task
            self._task = None
