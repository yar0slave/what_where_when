from aiohttp.web import run_app

from app.web.app import setup_app

if __name__ == "__main__":
    app = setup_app()
    run_app(app, host='localhost', port=8080)
