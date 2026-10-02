import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app.handlers.start import router as start_router
from app.handlers.tickets import router as tickets_router
from app.handlers.my_tickets import router as my_tickets_router
from app.handlers.help import router as help_router
from app.core.logging_config import setup_logging

load_dotenv()


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))

    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(tickets_router)
    dp.include_router(my_tickets_router)
    dp.include_router(help_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())