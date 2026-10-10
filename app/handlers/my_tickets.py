from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.exc import SQLAlchemyError
from aiogram.filters import StateFilter

from db.queries import get_user_tickets


router = Router()


@router.message(
    StateFilter(None),
    F.text == "Мои заявки"
)
async def my_tickets(message: Message):

    if message.from_user is None:
        return

    try:
        tickets = await get_user_tickets(
            telegram_user_id=message.from_user.id
        )

    except SQLAlchemyError:
        await message.answer(
            "Не удалось загрузить заявки. Попробуйте позже."
        )
        return

    if not tickets:
        await message.answer(
            "У вас пока нет заявок."
        )
        return

    status_names = {
        "new": "🆕 Новая",
        "in_progress": "🔄 В работе",
        "closed": "✅ Закрыта",
    }

    for ticket in tickets:
        status = status_names.get(
            ticket.status,
            "Неизвестный статус"
        )

        await message.answer(
            f"📋 Заявка №{ticket.id}\n"
            f"Название: {ticket.title}\n"
            f"Категория: {ticket.category}\n"
            f"Статус: {status}"
        )