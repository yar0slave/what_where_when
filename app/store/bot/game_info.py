import asyncio
import random
from dataclasses import dataclass

from app.store.bot.registration import Player


@dataclass
class Question:
    text: str
    answer: str


class Statistics:
    def __init__(
        self,
        participants: dict[int, Player | None],
        tg_client,
        chat_id: int
    ):
        self.participants = participants
        self.captain: str | None = None
        self.score_team = 0
        self.score_bot = 0
        self.rounds = 5
        self.current_question: Question | None = None
        self.answering_player: str | None = None
        self.is_accepting_answer = False
        self.discussion_time = 60
        self.tg_client = tg_client
        self.chat_id = chat_id
        self.current_round = 0
        self.round_complete = asyncio.Event()  # Для синхронизации раундов
        self.questions = [
            Question(
                "Что находится между Землей и Солнцем?",
                "и"
            ),
            Question(
                "Какое слово начинается с буквы К и обозначает вид транспорта?",
                "корабль"
            ),
            Question(
                "В каком году произошло крещение Руси?",
                "988"
            ),
            Question(
                "Назовите самую маленькую планету Солнечной системы.",
                "меркурий"
            ),
            Question(
                "Какой химический элемент обозначается символом Au?",
                "золото"
            ),
        ]

    async def get_captain(self) -> str:
        for player in self.participants.values():
            if player.is_captain:
                return player.username
        return "Капитан не найден"

    async def start_game(self):
        self.captain = await self.get_captain()
        rules = (
            "🎮 Правила игры «Что? Где? Когда?»:\n\n"
            "1️⃣ Игра состоит из 5 раундов\n"
            "2️⃣ В каждом раунде команде задается вопрос\n"
            "3️⃣ У команды есть 1 минута на обсуждение\n"
            "4️⃣ После обсуждения капитан выбирает отвечающего командой "
            "/choose @username\n"
            "5️⃣ У выбранного игрока есть 20 секунд на ответ\n"
            "6️⃣ За правильный ответ команда получает 1 балл\n"
            "7️⃣ За неправильный ответ или отсутствие "
            "ответа балл получает бот\n\n"
            f"👑 Капитан команды: @{self.captain}\n"
            f"🎯 Количество раундов: {self.rounds}"
        )
        await self.tg_client.send_message(self.chat_id, rules)
        await asyncio.sleep(5)
        await self.tg_client.send_message(
            self.chat_id,
            "🎲 Игра начинается! Приготовьтесь к первому вопросу..."
        )

    async def play_round(self, round_number: int):
        self.round_complete.clear()
        self.current_round = round_number

        if not self.questions:
            await self.tg_client.send_message(
                self.chat_id,
                "❌ Закончились вопросы! Игра завершается досрочно."
            )
            self.round_complete.set()
            return False

        self.current_question = random.choice(self.questions)
        self.questions.remove(self.current_question)

        round_announcement = (
            f"🎯 Раунд {round_number}\n"
            f"💭 Вопрос: {self.current_question.text}\n\n"
            f"⏳ Время на обсуждение: {self.discussion_time} секунд"
        )
        await self.tg_client.send_message(self.chat_id, round_announcement)

        await asyncio.sleep(self.discussion_time - 10)
        await self.tg_client.send_message(
            self.chat_id,
            "⚠️ 10 секунд до окончания обсуждения!"
        )
        await asyncio.sleep(10)

        await self.tg_client.send_message(
            self.chat_id,
            f"👑 @{self.captain}, "
            f"выберите отвечающего командой /choose @username"
        )

        self.is_accepting_answer = False
        self.answering_player = None

        await self.round_complete.wait()
        return True

    async def handle_captain_choice(self, chosen_username: str) -> bool:
        if not self.current_round:
            return False

        chosen_player = next(
            (
                player
                for player in self.participants.values()
                if player.username == chosen_username
            ),
            None
        )

        if not chosen_player:
            await self.tg_client.send_message(
                self.chat_id,
                "❌ Выбранный игрок не участвует в игре!"
            )
            return False

        self.answering_player = chosen_username
        self.is_accepting_answer = True

        await self.tg_client.send_message(
            self.chat_id,
            f"🎯 @{chosen_username}, ваш ответ?"
            f" Формат ответа: /answer ваш_ответ"
        )
        return True

    async def handle_answer(self, username: str, answer: str) -> bool:
        if not self.is_accepting_answer:
            return False

        if username != self.answering_player:
            await self.tg_client.send_message(
                self.chat_id,
                "❌ Сейчас не ваша очередь отвечать!"
            )
            return False

        self.is_accepting_answer = False

        if (answer.lower().strip() ==
                self.current_question.answer.lower().strip()):
            self.score_team += 1
            await self.tg_client.send_message(
                self.chat_id,
                "✅ Правильный ответ! Команда получает балл."
            )
        else:
            self.score_bot += 1
            await self.tg_client.send_message(
                self.chat_id,
                f"❌ Неправильно!"
                f" Правильный ответ: {self.current_question.answer}"
            )

        await self.tg_client.send_message(
            self.chat_id,
            f"📊 Счет: Команда {self.score_team} - {self.score_bot} Бот"
        )

        self.round_complete.set()
        return True

    async def finish_game(self):
        final_message = "🏁 Игра окончена!\n\n"

        if self.score_team > self.score_bot:
            final_message += (
                "🏆 Поздравляем! Команда знатоков победила!\n"
                f"Финальный счет: {self.score_team} - {self.score_bot}"
            )
        elif self.score_team < self.score_bot:
            final_message += (
                "😔 Команда знатоков проиграла.\n"
                f"Финальный счет: {self.score_team} - {self.score_bot}"
            )
        else:
            final_message += (
                "🤝 Ничья! Отличная игра!\n"
                f"Финальный счет: {self.score_team} - {self.score_bot}"
            )

        await self.tg_client.send_message(self.chat_id, final_message)
