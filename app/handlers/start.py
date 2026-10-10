from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.filters import StateFilter

from app.keyboards.main_menu import main_keyboard
from db.queries import get_or_create_user

router = Router()


@router.message(
    StateFilter(None),
    CommandStart()
)
async def start_handler(message: Message):

    tg_user = message.from_user

    if tg_user is None:
        return

    await get_or_create_user(
        telegram_user_id=tg_user.id,
        username=tg_user.username,
        full_name=tg_user.full_name,
    )

    await message.answer(
        "Добро пожаловать в Service Desk!\n"
        "Выберите действие:",
        reply_markup=main_keyboard,
    )