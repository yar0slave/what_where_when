import asyncio
import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application
from app.store.bot.messages import (
    CHOOSE_PLAYER_TEXT,
    CORRECT_ANSWER_TEXT,
    DISCUSSION_WARNING_TEXT,
    FINAL_DRAW_TEXT,
    FINAL_LOSE_TEXT,
    FINAL_WIN_TEXT,
    NOT_YOUR_TURN_TEXT,
    PLAYER_ANSWER_PROMPT,
    PLAYER_NOT_FOUND_TEXT,
    ROUND_ANNOUNCEMENT_TEMPLATE,
    RULES_TEXT,
    SCORE_TEXT,
    START_TEXT,
    WRONG_ANSWER_TEXT,
)


class Statistics:
    def __init__(self, tg_client, chat_id: int, app: "Application"):
        self.rounds = 3
        self.app = app
        self.discussion_time = 60
        self.tg_client = tg_client
        self.chat_id = chat_id
        self.round_complete = None  # Remove the initialization here

    async def start_game(self):
        captain = await self.app.store.creategame.is_captain_set(self.chat_id)
        rules = RULES_TEXT.format(captain=captain, rounds=self.rounds)
        await self.tg_client.send_message(self.chat_id, rules)
        await asyncio.sleep(5)
        await self.tg_client.send_message(self.chat_id, START_TEXT)

    async def play_round(self, round_number: int):
        self.round_complete = asyncio.Event()

        await self.app.store.creategame.set_round_number(
            self.chat_id, round_number
        )

        question = await self.app.store.quiz.get_random_unasked_question(
            self.chat_id
        )
        await self.app.store.quiz.mark_question_as_asked(
            self.chat_id, question.id
        )
        await self.app.store.creategame.assign_question_to_game(
            question.question, self.chat_id
        )

        round_announcement = ROUND_ANNOUNCEMENT_TEMPLATE.format(
            round_number=round_number,
            question_text=question.question,
            discussion_time=self.discussion_time,
        )
        await self.tg_client.send_message(self.chat_id, round_announcement)

        await asyncio.sleep(self.discussion_time - 10)
        await self.tg_client.send_message(self.chat_id, DISCUSSION_WARNING_TEXT)
        await asyncio.sleep(10)

        captain = await self.app.store.creategame.is_captain_set(self.chat_id)
        await self.tg_client.send_message(
            self.chat_id,
            CHOOSE_PLAYER_TEXT.format(captain=captain),
        )

        await self.round_complete.wait()
        self.round_complete.clear()
        return True

    async def handle_answer(self, username: str, answer: str) -> bool:
        choosen_player = (
            await self.app.store.creategame.get_respondent_id_by_chat_id(
                self.chat_id
            )
        )
        if not choosen_player:
            return False

        if username != choosen_player:
            await self.tg_client.send_message(self.chat_id, NOT_YOUR_TURN_TEXT)
            return False

        await (self.app.store.creategame.reset_respondent_id(
            code_of_chat=self.chat_id))

        question = await self.app.store.creategame.get_question_by_chat_id(
            self.chat_id
        )
        score_team = (
            await self.app.store.creategame.get_points_awarded_by_chat_id(
                self.chat_id
            )
        )

        if answer.lower().strip() == question.answer.lower().strip():
            await self.app.store.creategame.create_or_update_game(
                code_of_chat=self.chat_id, points_awarded=score_team + 1
            )
            await self.tg_client.send_message(self.chat_id, CORRECT_ANSWER_TEXT)
        else:
            await self.tg_client.send_message(
                self.chat_id,
                WRONG_ANSWER_TEXT.format(correct_answer=question.answer),
            )

        score_team = (
            await self.app.store.creategame.get_points_awarded_by_chat_id(
                self.chat_id
            )
        )
        now_rounds = (
            await self.app.store.creategame.get_round_number_by_chat_id(
                self.chat_id
            )
        )
        await self.tg_client.send_message(
            self.chat_id,
            SCORE_TEXT.format(
                team_score=score_team, bot_score=abs(now_rounds - score_team)
            ),
        )

        if self.round_complete is not None:
            self.round_complete.set()
        return True

    async def handle_captain_choice(self, chosen_username: str) -> bool:
        choosen_player = (
            await self.app.store.creategame.get_respondent_id_by_chat_id(
                self.chat_id
            )
        )
        if choosen_player:
            return False

        participants = await self.app.store.users.get_users_by_chat_id(
            self.chat_id
        )

        chosen_player = next(
            (player for player in participants if player == chosen_username),
            None,
        )

        if not chosen_player:
            await self.tg_client.send_message(
                self.chat_id, PLAYER_NOT_FOUND_TEXT
            )
            return False

        await self.app.store.creategame.create_or_update_game(
            code_of_chat=self.chat_id, respondent_id=chosen_username
        )

        await self.tg_client.send_message(
            self.chat_id,
            PLAYER_ANSWER_PROMPT.format(player=chosen_username),
        )
        return True

    async def finish_game(self):
        score_team = (
            await self.app.store.creategame.get_points_awarded_by_chat_id(
                self.chat_id
            )
        )
        now_rounds = (
            await self.app.store.creategame.get_round_number_by_chat_id(
                self.chat_id
            )
        )
        score_bot = abs(now_rounds - score_team)
        if score_team > score_bot:
            final_message = FINAL_WIN_TEXT.format(
                team_score=score_team, bot_score=score_bot
            )
        elif score_team < score_bot:
            final_message = FINAL_LOSE_TEXT.format(
                team_score=score_team, bot_score=score_bot
            )
        else:
            final_message = FINAL_DRAW_TEXT.format(
                team_score=score_team, bot_score=score_bot
            )

        await self.tg_client.send_message(self.chat_id, final_message)
        await self.app.store.creategame.create_or_update_game(
            code_of_chat=self.chat_id, is_working=0
        )
