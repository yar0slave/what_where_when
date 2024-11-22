import random
from dataclasses import dataclass


@dataclass
class Player:
    username: str
    user_id: int
    is_captain: bool = False


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
        message = (
            "🎮 Начинается регистрация на игру «Что? Где? Когда?»\n\n"
            "📝 Чтобы присоединиться к игре, отправьте команду /join\n"
            f"ℹ️ Требуется до {self.max_players} игроков\n"
            "❌ Для завершения регистрации"
            " администратор может отправить /finish_reg"
        )
        await self.tg_client.send_message(self.chat_id, message)

    async def add_player(self, user_id: int,
                         username: str, is_captain: bool = False) -> bool:
        if not self.registration_open:
            await self.tg_client.send_message(
                self.chat_id,
                "❌ Регистрация сейчас закрыта"
            )
            return False

        if len(self.players) >= self.max_players:
            await self.tg_client.send_message(
                self.chat_id,
                "❌ Достигнуто максимальное количество игроков"
            )
            return False

        if user_id in self.players:
            await self.tg_client.send_message(
                self.chat_id,
                "❌ Вы уже зарегистрированы"
            )
            return False

        self.players[user_id] = (
            Player(username=username, user_id=user_id, is_captain=is_captain))

        await self.tg_client.send_message(
            self.chat_id,
            (
                f"✅ @{username} зарегистрирован!\n"
                f"👥 Количество игроков: {len(self.players)}/{self.max_players}"
            )
        )
        return True

    async def finish_registration(self) -> bool:
        if not self.registration_open:
            await self.tg_client.send_message(
                self.chat_id,
                "❌ Регистрация уже закрыта"
            )
            return False

        self.registration_open = False

        captain = random.choice(list(self.players.keys()))

        self.players[captain].is_captain = True

        players_list = [
            (f"{'👑 Капитан' if player.is_captain else '👤 Игрок'}: "
             f"@{player.username}")
            for player in self.players.values()
        ]

        final_message = (
            "✅ Регистрация завершена!\n\n"
            "Состав команды:\n" +
            "\n".join(players_list) +
            f"\n\nВсего игроков: {len(self.players)}"
        )

        await self.tg_client.send_message(self.chat_id, final_message)
        return True

    def get_players(self) -> dict[int, Player]:
        return self.players
