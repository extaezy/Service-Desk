
import logging
import httpx

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import StateFilter

from app.api_client.tickets import get_user_tickets


router = Router()
logger = logging.getLogger(__name__)


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

    except (httpx.HTTPStatusError, httpx.RequestError):
        logger.exception("Ошибка получения заявок через API")
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

    category_names = {
        "hardware": "Оборудование",
        "software": "Программное обеспечение",
        "network": "Сеть и интернет",
        "other": "Другое",
    }

    for ticket in tickets:
        status = status_names.get(
            ticket["status"],
            "Неизвестный статус"
        )

        category = category_names.get(
            ticket["category"],
            ticket["category"]
        )

        await message.answer(
            f"📋 Заявка №{ticket['id']}\n"
            f"Название: {ticket['title']}\n"
            f"Категория: {category}\n"
            f"Статус: {status}"
        )
