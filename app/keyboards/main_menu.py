from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Создать заявку")],
        [KeyboardButton(text="Мои заявки")],
        [KeyboardButton(text="Помощь")],
    ],
    resize_keyboard=True,
)