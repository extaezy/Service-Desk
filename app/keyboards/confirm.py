from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


confirm_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Всё верно.",
                callback_data="ticket:confirm"
            )
        ]
    ]
)