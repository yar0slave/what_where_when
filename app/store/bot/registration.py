import random

from app.store.bot.dataclasses import Player
from app.store.bot.messages import (
    ALREADY_REGISTERED_TEXT,
    MAX_PLAYERS_REACHED_TEXT,
    PLAYER_REGISTERED_TEXT,
    REGISTRATION_ALREADY_CLOSED_TEXT,
    REGISTRATION_CLOSED_TEXT,
    REGISTRATION_FINISHED_TEXT,
    REGISTRATION_START_TEXT,
)


class GameRegistration:
    def __init__(self, tg_client, chat_id: int):
        self.tg_client = tg_client
        self.chat_id = chat_id
        self.players: dict[int, Player] = {}
        self.registration_open = False
        self.max_players = 12

    async def start_registration(self):
        self.registration_open = True
        self.players.clear()
        message = REGISTRATION_START_TEXT.format(max_players=self.max_players)
        await self.tg_client.send_message(self.chat_id, message)

    async def add_player(
        self, user_id: int, username: str, is_captain: bool = False
    ) -> bool:
        if not self.registration_open:
            await self.tg_client.send_message(
                self.chat_id, REGISTRATION_CLOSED_TEXT
            )
            return False

        if len(self.players) >= self.max_players:
            await self.tg_client.send_message(
                self.chat_id, MAX_PLAYERS_REACHED_TEXT
            )
            return False

        if user_id in self.players:
            await self.tg_client.send_message(
                self.chat_id, ALREADY_REGISTERED_TEXT
            )
            return False

        self.players[user_id] = Player(
            username=username, user_id=user_id, is_captain=is_captain
        )

        await self.tg_client.send_message(
            self.chat_id,
            PLAYER_REGISTERED_TEXT.format(
                username=username,
                current_players=len(self.players),
                max_players=self.max_players,
            ),
        )
        return True

    async def finish_registration(self) -> bool:
        if not self.registration_open:
            await self.tg_client.send_message(
                self.chat_id, REGISTRATION_ALREADY_CLOSED_TEXT
            )
            return False

        self.registration_open = False

        captain = random.choice(list(self.players.keys()))
        self.players[captain].is_captain = True

        players_list = [
            (
                f"{'👑 Капитан' if player.is_captain else '👤 Игрок'}: "
                f"@{player.username}"
            )
            for player in self.players.values()
        ]
        final_message = REGISTRATION_FINISHED_TEXT.format(
            players_list="\n".join(players_list),
            total_players=len(self.players),
        )

        await self.tg_client.send_message(self.chat_id, final_message)
        return True

    def get_players(self) -> dict[int, Player]:
        return self.players
