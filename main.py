import os

from aiohttp.web import run_app

from app.web.app import setup_app

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

if __name__ == "__main__":
    run_app(setup_app())
