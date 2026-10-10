from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)


admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🆕 Новые заявки"),
            KeyboardButton(text="🔄 В работе"),
        ],
        [
            KeyboardButton(
                text="🚪 Выйти из режима администратора"
            )
        ]
    ],
    resize_keyboard=True
)