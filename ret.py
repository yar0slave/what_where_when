import asyncio
from app.store.bot.poller import Poller


async def test_poller():
    queue = asyncio.Queue()
    poller = Poller("7261082770:AAEi5vpiQx9LFro1EjZpcsloRsky0NL45eU", queue)
    await poller.start()

    await asyncio.sleep(20)  # Даем `Poller` больше времени для тестирования
    await poller.stop()

if __name__ == "__main__":
    asyncio.run(test_poller())
