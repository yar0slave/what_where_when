import random
import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application
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
    def __init__(self, tg_client, chat_id: int, app: "Application"):
        self.tg_client = tg_client
        self.app = app
        self.chat_id = chat_id
        self.max_players = 12

    async def start_registration(self):
        message = REGISTRATION_START_TEXT.format(max_players=self.max_players)
        await self.tg_client.send_message(self.chat_id, message)

    async def add_player(
            self, user_id: int, username: str
    ) -> bool:

        players = await self.app.store.users.get_users_by_chat_id(self.chat_id)
        registration_open = not (await self.app.store.creategame.is_captain_set(self.chat_id))
        if not registration_open:
            await self.tg_client.send_message(
                self.chat_id, REGISTRATION_CLOSED_TEXT
            )
            return False

        if len(players) >= self.max_players:
            await self.tg_client.send_message(
                self.chat_id, MAX_PLAYERS_REACHED_TEXT
            )
            return False

        if username in players:
            await self.tg_client.send_message(
                self.chat_id, ALREADY_REGISTERED_TEXT
            )
            return False

        await self.app.store.users.join_user(user_id, username, self.chat_id)

        await self.tg_client.send_message(
            self.chat_id,
            PLAYER_REGISTERED_TEXT.format(
                username=username,
                current_players=len(players) + 1,
                max_players=self.max_players,
            ),
        )
        return True

    async def finish_registration(self) -> bool:
        registration_open = not (await self.app.store.creategame.is_captain_set(self.chat_id))
        if not registration_open:
            await self.tg_client.send_message(
                self.chat_id, REGISTRATION_ALREADY_CLOSED_TEXT
            )
            return False

        players = await self.app.store.users.get_users_by_chat_id(self.chat_id)
        captain = random.choice(list(players))

        await self.app.store.creategame.create_or_update_game(code_of_chat=self.chat_id, captain_id=captain)

        players_list = [
            f"👑 Капитан @{captain}"
        ]
        for player in players:
            if player != captain:
                players_list.append(f"👤 Игрок: @{player.username}")

        final_message = REGISTRATION_FINISHED_TEXT.format(
            players_list="\n".join(players_list),
            total_players=len(players),
        )

        await self.tg_client.send_message(self.chat_id, final_message)
        return True
