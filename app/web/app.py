from aiohttp.web import (
    Application as AiohttpApplication,
)

from app.store import Store, setup_store
from app.web.logger import setup_logging
from .routes import setup_routes
from app.web.config import Config, setup_config


class Application(AiohttpApplication):
    config = None
    store: Store | None = None
    database = None


app = Application()


def setup_app() -> Application:
    setup_logging(app)
    setup_config(app)
    setup_routes(app)
    setup_store(app)
    return app
