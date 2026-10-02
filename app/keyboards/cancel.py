from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⬅️ Назад"),
            KeyboardButton(text="❌ Отменить создание")
        ]
    ],
    resize_keyboard=True,
    is_persistent=True
)