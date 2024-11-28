import asyncio
import logging
import typing
from typing import Dict

if typing.TYPE_CHECKING:
    from app.web.app import Application
from app.store.bot.game_info import Statistics
from app.store.bot.messages import (
    GAME_IN_PROGRESS_TEXT,
    HELP_TEXT,
    ONLY_CAPTAIN_TEXT,
    REGISTRATION_CLOSED_TEXT,
    STATISTICS_TEXT,
)
from app.store.bot.registration import GameRegistration
from clients.tg import TgClient
from clients.tg.dcs import UpdateObj


class Worker:
    def __init__(self, token: str, queue: asyncio.Queue, app: "Application"):
        self.tg_client = TgClient(token)
        self.app = app
        self.queue = queue
        self._tasks: list[asyncio.Task] = []
        self.games: Dict[int, GameRegistration | Statistics] = {}  # Store games by chat_id

    async def start_game_rounds(self, chat_id: int):
        game = self.games.get(chat_id)
        if not game or not isinstance(game, Statistics):
            return

        try:
            for i in range(1, game.rounds + 1):
                if not await game.play_round(i):
                    break
                await asyncio.sleep(2)
        except Exception as e:
            logging.error("Error in game rounds for chat %d: %s", chat_id, e)
        finally:
            await game.finish_game()
            if chat_id in self.games:
                del self.games[chat_id]

    async def handle_start(self, chat_id: int):
        codes = await self.app.store.creategame.get_all_code_of_chat()
        if chat_id in codes and await self.app.store.creategame.is_game_working(chat_id):
            await self.tg_client.send_message(chat_id, GAME_IN_PROGRESS_TEXT)
            return

        await self.app.store.creategame.clear_game_users_and_asked_questions(chat_id)
        await self.app.store.creategame.create_or_update_game(
            code_of_chat=chat_id, is_working=1
        )
        self.games[chat_id] = GameRegistration(self.tg_client, chat_id, self.app)
        await self.games[chat_id].start_registration()

    async def handle_join(self, chat_id: int, user_id: int, username: str):
        if chat_id not in self.games:
            return

        game = self.games[chat_id]
        if not isinstance(game, GameRegistration):
            await self.tg_client.send_message(chat_id, GAME_IN_PROGRESS_TEXT)
            return

        await game.add_player(user_id, username)

    async def handle_finish_reg(self, chat_id: int):
        if chat_id not in self.games:
            return

        game = self.games[chat_id]
        if not isinstance(game, GameRegistration):
            return

        if await game.finish_registration():
            self.games[chat_id] = Statistics(self.tg_client, chat_id, self.app)
            await self.games[chat_id].start_game()

            task = asyncio.create_task(self.start_game_rounds(chat_id))
            self._tasks.append(task)

    async def handle_choose(self, chat_id: int, username: str, text: str):
        game = self.games.get(chat_id)
        if not game or not isinstance(game, Statistics):
            await self.tg_client.send_message(chat_id, REGISTRATION_CLOSED_TEXT)
            return

        captain = await self.app.store.creategame.is_captain_set(chat_id)
        if username != captain:
            await self.tg_client.send_message(chat_id, ONLY_CAPTAIN_TEXT)
            return

        chosen_player = text.split("/choose ", 1)[1].strip().lstrip("@")
        await game.handle_captain_choice(chosen_player)

    async def handle_answer(self, chat_id: int, username: str, text: str):
        game = self.games.get(chat_id)
        if not game or not isinstance(game, Statistics):
            return

        answer = text.split("/answer ", 1)[1].strip()
        await game.handle_answer(username, answer)

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
        elif text.startswith("/choose "):
            await self.handle_choose(chat_id, username, text)
        elif text.startswith("/answer "):
            await self.handle_answer(chat_id, username, text)
        elif text == "/help":
            await self.handle_help(chat_id)
        elif text == "/stat":
            await self.print_statictics(chat_id)

    async def handle_help(self, chat_id: int):
        await self.tg_client.send_message(chat_id, HELP_TEXT)

    async def print_statictics(self, chat_id: int):
        codes = await self.app.store.creategame.get_all_code_of_chat()
        if chat_id in codes:
            if await self.app.store.creategame.is_game_working(chat_id):
                await self.tg_client.send_message(chat_id, GAME_IN_PROGRESS_TEXT)
                return

            score_team = await self.app.store.creategame.get_points_awarded_by_chat_id(chat_id)
            await self.tg_client.send_message(chat_id, STATISTICS_TEXT.format(score_team=score_team))

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