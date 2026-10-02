from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


category_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Оборудование",
                callback_data="category:hardware"
            )
        ],
        [
            InlineKeyboardButton(
                text="Программное обеспечение",
                callback_data="category:software"
            )
        ],
        [
            InlineKeyboardButton(
                text="Сеть и интернет",
                callback_data="category:network"
            )
        ],
        [
            InlineKeyboardButton(
                text="Другое",
                callback_data="category:other"
            )
        ],
    ]
)