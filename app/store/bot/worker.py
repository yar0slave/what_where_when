import asyncio
import logging

from clients.tg import TgClient
from clients.tg.dcs import UpdateObj
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class Worker:
    def __init__(
            self,
            token: str,
            queue: asyncio.Queue,
    ):
        self.tg_client = TgClient(token)
        self.queue = queue
        self._tasks: list[asyncio.Task] = []

    async def handle_update(self, upd: UpdateObj):
        if upd.message:
            text = upd.message.text
            chat_id = upd.message.chat.id
            if text == "/start":
                if upd.message.chat.type in ["group", "supergroup"]:
                    members = await self.tg_client.get_group_members(chat_id)
                    members_text = "\n".join(members)

                    await self.tg_client.send_message(
                        chat_id, f"Участники группы:\n{members_text}"
                    )
            else:
                logging.info("Processing message: %s", text)
                await self.tg_client.send_message(
                    chat_id, f"написали: {text}"
                )
        else:
            logging.warning("Пропущено обновление без сообщения: %s", upd)

    async def _worker(self):
        try:
            while True:
                upd = await self.queue.get()
                try:
                    await self.handle_update(upd)
                finally:
                    self.queue.task_done()
        except asyncio.CancelledError:
            logging.warning("Worker loop was cancelled.")
            raise

    async def start(self):
        self._tasks = [asyncio.create_task(self._worker())]

    async def stop(self):
        await self.queue.join()  # Ждем, пока очередь будет обработана
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        logging.info("Worker tasks завершены.")
