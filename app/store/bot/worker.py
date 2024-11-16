import asyncio
import datetime
from typing import List

from clients.tg import TgClient
from clients.tg.dcs import UpdateObj


class Worker:
    def __init__(self, token: str, queue: asyncio.Queue, concurrent_workers: int):
        self.tg_client = TgClient(token)
        self.queue = queue
        self.concurrent_workers = concurrent_workers
        self._tasks: List[asyncio.Task] = []

    async def handle_update(self, upd: UpdateObj):
        print("before", upd.message.text, datetime.datetime.now())
        print("after", upd.message.text, datetime.datetime.now())
        await self.tg_client.send_message(upd.message.chat.id, upd.message.text)

    async def _worker(self):
        try:
            while True:
                upd = await self.queue.get()
                try:
                    await self.handle_update(upd)
                finally:
                    self.queue.task_done()
        except asyncio.CancelledError:
            print("Worker loop was cancelled.")
            raise

    async def start(self):
        self._tasks = [asyncio.create_task(self._worker()) for _ in range(self.concurrent_workers)]

    async def stop(self):
        await self.queue.join()  # Ждем, пока очередь будет обработана
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        print("Worker tasks завершены.")

