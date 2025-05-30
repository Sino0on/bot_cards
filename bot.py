import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from decouple import config
from handlers import photo_handler, manager_handler, start_handler



bot = Bot(token=config('BOT_TOKEN'))
dp = Dispatcher()



async def main():
    dp.include_router(manager_handler.router)
    dp.include_router(photo_handler.router)
    dp.include_router(start_handler.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
