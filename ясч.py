import asyncio
import logging

from app.web.app import setup_app

logging.basicConfig(level=logging.DEBUG)

asyncio.run(setup_app("test"))
