import asyncio
import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.bot.base import Bot

        self.app = app
        self.bots_manager = Bot(token="7261082770:AAEi5vpiQx9LFro1EjZpcsloRsky0NL45eU", n=2)


def setup_store(app: "Application"):
    app.store = Store(app)

    async def on_startup(app: "Application"):
        await app.store.bots_manager.start()

    async def on_cleanup(app: "Application"):
        try:
            await app.store.bots_manager.stop()
            print("Bots manager cleanup завершен.")
        except Exception as e:
            print(f"Ошибка в on_cleanup: {e}")

        pending_tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
        for task in pending_tasks:
            print(f"Ожидаем завершения задачи: {task}")
        await asyncio.gather(*pending_tasks, return_exceptions=True)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
