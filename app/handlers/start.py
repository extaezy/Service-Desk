from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.main_menu import main_keyboard


router = Router()


# Старт
@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Добро пожаловать в Service Desk!\n"
        "Выберите действие:",
        reply_markup=main_keyboard,
    )