import logging
import httpx

from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.filters import Command
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.fsm.context import FSMContext

from app.states.admin_state import AdminState
from app.api_client.tickets import (
    get_admin_tickets,
    update_ticket_status,
)
from app.keyboards.admin_keyboard import admin_keyboard
from app.keyboards.main_menu import main_keyboard

from app.api_client.users import is_admin


router = Router()
logger = logging.getLogger(__name__)


STATUS_NAMES = {
    "new": "🆕 Новая",
    "in_progress": "🔄 В работе",
    "closed": "✅ Закрыта",
}

CATEGORY_NAMES = {
    "hardware": "Оборудование",
    "software": "Программное обеспечение",
    "network": "Сеть и интернет",
    "other": "Другое",
}


@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    if message.from_user is None:
        return

    if not await is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return

    await state.set_state(AdminState.active)

    await message.answer(
        "🛠 Панель администратора Service Desk\n"
        "Выберите раздел:",
        reply_markup=admin_keyboard
    )


@router.message(F.text == "🆕 Новые заявки")
async def admin_new_tickets(message: Message):
    if message.from_user is None:
        return

    if not await is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        return

    await show_admin_tickets(message, "new")


@router.message(F.text == "🔄 В работе")
async def admin_in_progress_tickets(message: Message):
    if message.from_user is None:
        return

    if not await is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        return

    await show_admin_tickets(message, "in_progress")


@router.message(F.text == "🚪 Выйти из режима администратора")
async def exit_admin(message: Message, state: FSMContext):

    await state.clear()

    await message.answer(
        "Вы вышли из режима администратора.",
        reply_markup=main_keyboard
    )


async def show_admin_tickets(
    message: Message,
    status: str
):
    try:
        tickets = await get_admin_tickets(
            status=status,
            admin_id=message.from_user.id
        )

    except Exception:
        logger.exception("Ошибка загрузки заявок администратора")
        await message.answer("Ошибка загрузки заявок")
        return

    if not tickets:
        await message.answer(
            "Заявок с таким статусом пока нет."
        )
        return

    for ticket in tickets:
        keyboard = None

        if ticket["status"] == "new":
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="✅ Взять в работу",
                        callback_data=f"admin:take:{ticket['id']}"
                    )
                ]]
            )

        elif ticket["status"] == "in_progress":
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="🔒 Закрыть заявку",
                        callback_data=f"admin:close:{ticket['id']}"
                    )
                ]]
            )

        await message.answer(
            format_ticket(ticket),
            reply_markup=keyboard
        )


def format_ticket(ticket: dict) -> str:
    status = STATUS_NAMES.get(
        ticket["status"],
        ticket["status"]
    )

    category = CATEGORY_NAMES.get(
        ticket["category"],
        ticket["category"]
    )

    return (
        f"📋 Заявка №{ticket['id']}\n"
        f"Название: {ticket['title']}\n"
        f"Категория: {category}\n"
        f"Описание: {ticket['description']}\n"
        f"Автор: {ticket['user']['full_name']}\n"
        f"Статус: {status}"
    )


async def update_ticket_message(
    callback: CallbackQuery,
    old_status: str,
    new_status: str,
):
    if callback.message is None:
        return

    old_text = callback.message.text or ""

    new_text = old_text.replace(
        f"Статус: {old_status}",
        f"Статус: {new_status}"
    )

    try:
        await callback.message.edit_text(
            new_text,
            reply_markup=None
        )

    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return

        logger.exception(
            "Ошибка обновления сообщения заявки"
        )



@router.callback_query(F.data.startswith("admin:take:"))
async def admin_take_ticket(
    callback: CallbackQuery,
    state: FSMContext
):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    try:
        ticket_id = int(callback.data.split(":")[-1])

    except (ValueError, AttributeError):
        await callback.answer(
            "Некорректный номер заявки",
            show_alert=True
        )
        return

    try:
        result = await update_ticket_status(
            ticket_id=ticket_id,
            status="in_progress",
            admin_id=callback.from_user.id
        )

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 409:
            await callback.answer(
                "Заявка уже обработана или недоступна",
                show_alert=True
            )
            return

        logger.exception(
            "Ошибка API при взятии заявки №%s",
            ticket_id
        )
        await callback.answer(
            "Ошибка при обновлении заявки",
            show_alert=True
        )
        return

    except httpx.RequestError:
        logger.exception("Нет соединения с FastAPI")
        await callback.answer(
            "Сервер недоступен",
            show_alert=True
        )
        return

    await update_ticket_message(
        callback,
        old_status="🆕 Новая",
        new_status="🔄 В работе"
    )

    await callback.answer()

    try:
        await callback.bot.send_message(
            chat_id=result["telegram_user_id"],
            text=(
                f"🔄 Ваша заявка №{ticket_id} "
                f"взята в работу."
            )
        )

    except TelegramAPIError:
        logger.exception(
            "Не удалось уведомить автора заявки №%s",
            ticket_id
        )


@router.callback_query(F.data.startswith("admin:close:"))
async def admin_close_ticket(
    callback: CallbackQuery,
    state: FSMContext
):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    try:
        ticket_id = int(callback.data.split(":")[-1])

    except (ValueError, AttributeError):
        await callback.answer(
            "Некорректный номер заявки",
            show_alert=True
        )
        return

    try:
        result = await update_ticket_status(
            ticket_id=ticket_id,
            status="closed",
            admin_id=callback.from_user.id
        )

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 409:
            await callback.answer(
                "Заявка уже закрыта или недоступна",
                show_alert=True
            )
            return

        logger.exception(
            "Ошибка API при закрытии заявки №%s",
            ticket_id
        )
        await callback.answer(
            "Ошибка при закрытии заявки",
            show_alert=True
        )
        return

    except httpx.RequestError:
        logger.exception("Нет соединения с FastAPI")
        await callback.answer(
            "Сервер недоступен",
            show_alert=True
        )
        return

    await update_ticket_message(
        callback,
        old_status="🔄 В работе",
        new_status="✅ Закрыта"
    )

    await callback.answer()

    try:
        await callback.bot.send_message(
            chat_id=result["telegram_user_id"],
            text=(
                f"✅ Ваша заявка №{ticket_id} закрыта.\n"
                "Спасибо за обращение!"
            )
        )

    except TelegramAPIError:
        logger.exception(
            "Не удалось уведомить автора о закрытии заявки №%s",
            ticket_id
        )



@router.message(AdminState.active)
async def admin_unknown_message(message: Message):
    await message.answer(
        "Вы находитесь в режиме администратора.\n"
        "Выберите действие на нижней клавиатуре "
        "или нажмите «Выйти из режима администратора»."
    )
