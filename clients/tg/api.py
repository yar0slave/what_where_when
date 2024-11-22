import aiohttp

from clients.tg.dcs import GetUpdatesResponse, SendMessageResponse


class TgClient:
    def __init__(self, token: str = ""):
        self.token = token

    def get_url(self, method: str):
        return f"https://api.telegram.org/bot{self.token}/{method}"

    async def get_me(self) -> dict:
        url = self.get_url("getMe")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()

    async def get_updates(
        self, offset: int | None = None, timeout: int = 0
    ) -> dict:
        url = self.get_url("getUpdates")
        params = {}
        if offset:
            params["offset"] = offset
        if timeout:
            params["timeout"] = timeout
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                return await resp.json()

    async def get_updates_in_objects(
        self, offset: int | None = None, timeout: int = 0
    ) -> GetUpdatesResponse:
        res_dict = await self.get_updates(offset=offset, timeout=timeout)
        return GetUpdatesResponse.Schema().load(res_dict)

    async def send_message(
        self, chat_id: int, text: str
    ) -> SendMessageResponse:
        url = self.get_url("sendMessage")
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                res_dict = await resp.json()
                return SendMessageResponse.Schema().load(res_dict)

    async def get_bot_username(self) -> str:
        bot_info = await self.get_me()
        return bot_info.get("result", "").get("username", "")

    async def get_group_members(self, chat_id: int) -> list[str]:
        members = []
        bot_username = await self.get_bot_username()
        async with aiohttp.ClientSession() as session:
            url = self.get_url("getChatAdministrators")
            params = {"chat_id": chat_id}
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                for member in data.get("result", []):
                    user = member["user"]
                    username = user.get("username")
                    if username != bot_username:
                        members.append(username)

        return members
