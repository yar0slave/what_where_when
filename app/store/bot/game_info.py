import asyncio
import random

from app.store.bot.dataclasses import Player, Question
from app.store.bot.messages import (
    CAPTAIN_NOT_FOUND_TEXT,
    CHOOSE_PLAYER_TEXT,
    CORRECT_ANSWER_TEXT,
    DISCUSSION_WARNING_TEXT,
    FINAL_DRAW_TEXT,
    FINAL_LOSE_TEXT,
    FINAL_WIN_TEXT,
    NOT_YOUR_TURN_TEXT,
    PLAYER_ANSWER_PROMPT,
    PLAYER_NOT_FOUND_TEXT,
    QUESTIONS_EMPTY_TEXT,
    ROUND_ANNOUNCEMENT_TEMPLATE,
    RULES_TEXT,
    SCORE_TEXT,
    START_TEXT,
    WRONG_ANSWER_TEXT,
)


class Statistics:
    def __init__(
        self, participants: dict[int, Player | None], tg_client, chat_id: int
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
            Question("Что находится между Землей и Солнцем?", "и"),
            Question(
                "Какое слово начинается с буквы К и обозначает вид транспорта?",
                "корабль",
            ),
            Question("В каком году произошло крещение Руси?", "988"),
            Question(
                "Назовите самую маленькую планету Солнечной системы.",
                "меркурий",
            ),
            Question(
                "Какой химический элемент обозначается символом Au?", "золото"
            ),
        ]

    async def get_captain(self) -> str:
        for player in self.participants.values():
            if player.is_captain:
                return player.username
        return CAPTAIN_NOT_FOUND_TEXT

    async def start_game(self):
        self.captain = await self.get_captain()
        rules = RULES_TEXT.format(captain=self.captain, rounds=self.rounds)
        await self.tg_client.send_message(self.chat_id, rules)
        await asyncio.sleep(5)
        await self.tg_client.send_message(self.chat_id, START_TEXT)

    async def play_round(self, round_number: int):
        self.round_complete.clear()
        self.current_round = round_number

        if not self.questions:
            await self.tg_client.send_message(
                self.chat_id, QUESTIONS_EMPTY_TEXT
            )
            self.round_complete.set()
            return False

        self.current_question = random.choice(self.questions)
        self.questions.remove(self.current_question)

        round_announcement = ROUND_ANNOUNCEMENT_TEMPLATE.format(
            round_number=round_number,
            question_text=self.current_question.text,
            discussion_time=self.discussion_time,
        )
        await self.tg_client.send_message(self.chat_id, round_announcement)

        await asyncio.sleep(self.discussion_time - 10)
        await self.tg_client.send_message(self.chat_id, DISCUSSION_WARNING_TEXT)
        await asyncio.sleep(10)

        await self.tg_client.send_message(
            self.chat_id,
            CHOOSE_PLAYER_TEXT.format(captain=self.captain),
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
            None,
        )

        if not chosen_player:
            await self.tg_client.send_message(
                self.chat_id, PLAYER_NOT_FOUND_TEXT
            )
            return False

        self.answering_player = chosen_username
        self.is_accepting_answer = True

        await self.tg_client.send_message(
            self.chat_id,
            PLAYER_ANSWER_PROMPT.format(player=chosen_username),
        )
        return True

    async def handle_answer(self, username: str, answer: str) -> bool:
        if not self.is_accepting_answer:
            return False

        if username != self.answering_player:
            await self.tg_client.send_message(self.chat_id, NOT_YOUR_TURN_TEXT)
            return False

        self.is_accepting_answer = False

        if (
            answer.lower().strip()
            == self.current_question.answer.lower().strip()
        ):
            self.score_team += 1
            await self.tg_client.send_message(self.chat_id, CORRECT_ANSWER_TEXT)
        else:
            self.score_bot += 1
            await self.tg_client.send_message(
                self.chat_id,
                WRONG_ANSWER_TEXT.format(
                    correct_answer=self.current_question.answer
                ),
            )

        await self.tg_client.send_message(
            self.chat_id,
            SCORE_TEXT.format(
                team_score=self.score_team, bot_score=self.score_bot
            ),
        )

        self.round_complete.set()
        return True

    async def finish_game(self):
        if self.score_team > self.score_bot:
            final_message = FINAL_WIN_TEXT.format(
                team_score=self.score_team, bot_score=self.score_bot
            )
        elif self.score_team < self.score_bot:
            final_message = FINAL_LOSE_TEXT.format(
                team_score=self.score_team, bot_score=self.score_bot
            )
        else:
            final_message = FINAL_DRAW_TEXT.format(
                team_score=self.score_team, bot_score=self.score_bot
            )

        await self.tg_client.send_message(self.chat_id, final_message)
