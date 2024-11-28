from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)

from app.store import Database, Store, setup_store
from app.web.config import setup_config
from app.web.logger import setup_logging
from app.web.routes import setup_routes


class Application(AiohttpApplication):
    config = None
    store: Store | None = None
    database = None


class Request(AiohttpRequest):
    @property
    def app(self) -> Application:
        return super().app()


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def database(self) -> Database:
        return self.request.app.database

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get("data", {})

    async def _iter(self):
        if self.request.content_type == "application/json":
            self.request["data"] = await self.request.json()
        return await super()._iter()


app = Application()


def setup_app() -> Application:
    setup_logging(app)
    setup_config(app)
    setup_routes(app)
    setup_store(app)
    return app
