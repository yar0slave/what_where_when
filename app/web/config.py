import os
import typing
from dataclasses import dataclass

from dotenv import load_dotenv

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
    port: str = "5432"  # Приведено к str, чтобы избежать PLW1508
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
    dotenv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        ".env",
    )
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    app.config = Config(
        session=SessionConfig(
            key=os.getenv("SESSION_KEY"),
        ),
        admin=AdminConfig(
            email=os.getenv("ADMIN_EMAIL"),
            password=os.getenv("ADMIN_PASSWORD"),
        ),
        bot=BotConfig(
            token=os.getenv("BOT_TOKEN"),
        ),
        database=DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            database=os.getenv("DB_NAME", "what"),
        ),
    )
