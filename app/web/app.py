from aiohttp.web import (
    Application as AiohttpApplication,
)

from .routes import setup_routes
from app.store import Store, setup_store


class Application(AiohttpApplication):
    config = None
    store: Store | None = None
    database = None


app = Application()


def setup_app(config_path: str) -> Application:
    setup_routes(app)
    setup_store(app)
    return app
