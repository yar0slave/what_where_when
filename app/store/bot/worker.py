import asyncio
import logging

from app.store.bot.game_info import Statistics
from app.store.bot.messages import (
    GAME_IN_PROGRESS_TEXT,
    HELP_TEXT,
    ONLY_CAPTAIN_TEXT,
)
from app.store.bot.registration import GameRegistration
from clients.tg import TgClient
from clients.tg.dcs import UpdateObj

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class Worker:
    def __init__(self, token: str, queue: asyncio.Queue):
        self.tg_client = TgClient(token)
        self.queue = queue
        self._tasks: list[asyncio.Task] = []
        self.games: dict[int, Statistics] = {}
        self.registrations: dict[int, GameRegistration] = {}

    async def start_game_rounds(self, chat_id: int):
        game = self.games[chat_id]
        try:
            for i in range(1, game.rounds + 1):
                if not await game.play_round(i):
                    break
                await asyncio.sleep(2)
        except Exception as e:
            logging.error("Error in game rounds: %s", e)
        finally:
            await game.finish_game()
            del self.games[chat_id]

    async def handle_start(self, chat_id: int):
        if chat_id in self.registrations or chat_id in self.games:
            await self.tg_client.send_message(chat_id, GAME_IN_PROGRESS_TEXT)
            return

        self.registrations[chat_id] = GameRegistration(self.tg_client, chat_id)
        await self.registrations[chat_id].start_registration()

    async def handle_join(self, chat_id: int, user_id: int, username: str):
        if chat_id in self.registrations:
            await self.registrations[chat_id].add_player(user_id, username)

    async def handle_finish_reg(self, chat_id: int):
        if (
            chat_id in self.registrations
            and await self.registrations[chat_id].finish_registration()
        ):
            members = self.registrations[chat_id].get_players()
            self.games[chat_id] = Statistics(members, self.tg_client, chat_id)
            await self.games[chat_id].start_game()
            del self.registrations[chat_id]

            task = asyncio.create_task(self.start_game_rounds(chat_id))
            self._tasks.append(task)

    async def handle_choose(self, chat_id: int, username: str, text: str):
        game = self.games[chat_id]

        if username != game.captain:
            await self.tg_client.send_message(chat_id, ONLY_CAPTAIN_TEXT)
            return

        chosen_player = text.split("/choose ", 1)[1].strip().lstrip("@")
        await game.handle_captain_choice(chosen_player)

    async def handle_answer(self, chat_id: int, username: str, text: str):
        game = self.games[chat_id]
        answer = text.split("/answer ", 1)[1].strip()
        await game.handle_answer(username, answer)

    async def handle_help(self, chat_id: int):
        await self.tg_client.send_message(chat_id, HELP_TEXT)

    async def handle_update(self, upd: UpdateObj):
        if not upd.message or not upd.message.text:
            return

        text = upd.message.text
        chat_id = upd.message.chat.id
        user_id = upd.message.from_.id
        username = upd.message.from_.username

        if text == "/start":
            await self.handle_start(chat_id)
        elif text == "/join":
            await self.handle_join(chat_id, user_id, username)
        elif text == "/finish_reg":
            await self.handle_finish_reg(chat_id)
        elif text.startswith("/choose ") and chat_id in self.games:
            await self.handle_choose(chat_id, username, text)
        elif text.startswith("/answer ") and chat_id in self.games:
            await self.handle_answer(chat_id, username, text)
        elif text == "/help":
            await self.handle_help(chat_id)

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
        await self.queue.join()
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        logging.info("Worker tasks завершены.")
