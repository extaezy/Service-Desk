from aiogram import Router, F
from aiogram.types import Message


router = Router()


@router.message(F.text == "Помощь")
async def help_handler(message: Message):
    await message.answer(
        "Service Desk помогает создавать "
        "и отслеживать обращения."
    )