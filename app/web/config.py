import typing
from dataclasses import dataclass
from dotenv import load_dotenv
import os
import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class SessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class BotConfig:
    token: str


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig | None = None
    bot: BotConfig | None = None
    database: DatabaseConfig | None = None


def setup_config(app: "Application"):
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    app.config = Config(
        session=SessionConfig(key=os.getenv("session_key")),
        admin=AdminConfig(
            email=os.getenv("admin_email"),
            password=os.getenv("admin_password"),
        ),
        bot=BotConfig(
            token=os.getenv("bot_token"),
        ),
        database=DatabaseConfig(),
    )

    print(app.config.bot.token)
