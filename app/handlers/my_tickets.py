from aiogram import Router, F
from aiogram.types import Message


router = Router()


@router.message(F.text == "Мои заявки")
async def my_tickets(message: Message):
    await message.answer(
        "Здесь будут отображаться ваши заявки."
    )