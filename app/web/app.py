from aiohttp.web import (
    Application as AiohttpApplication,
)

from app.store import Store, setup_store

from .routes import setup_routes


class Application(AiohttpApplication):
    config = None
    store: Store | None = None
    database = None


app = Application()


def setup_app() -> Application:
    setup_routes(app)
    setup_store(app)
    return app
