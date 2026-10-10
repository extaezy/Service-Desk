import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.fsm.context import FSMContext

from app.states.admin_state import AdminState
from sqlalchemy.exc import SQLAlchemyError
from db.queries import is_admin
from db.queries import get_admin_tickets
from db.queries import take_ticket
from db.queries import close_ticket
from db.queries import get_telegram_id

from app.keyboards.admin_keyboard import admin_keyboard
from app.keyboards.main_menu import main_keyboard

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):

    if message.from_user is None:
        return

    if not await is_admin(message.from_user.id):
        await message.answer(
            "У вас нет прав администратора."
        )
        return

    await state.set_state(AdminState.active)

    await message.answer(
        "🛠 Панель администратора Service Desk\n"
        "Выберите раздел:",
        reply_markup=admin_keyboard
    )


@router.message(
    AdminState.active,
    F.text == "🆕 Новые заявки"
)
async def admin_new_tickets(message: Message):

    if not await is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        return

    await show_admin_tickets(message, "new")


@router.message(
    AdminState.active,
    F.text == "🔄 В работе"
)
async def admin_in_progress_tickets(message: Message):

    if not await is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        return

    await show_admin_tickets(message, "in_progress")

@router.message(
    AdminState.active,
    F.text == "🚪 Выйти из режима администратора"
)
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
        tickets = await get_admin_tickets(status)

    except SQLAlchemyError:
        logger.exception("Ошибка загрузки заявок")
        await message.answer("Ошибка загрузки заявок")
        return

    if not tickets:
        await message.answer(
            "Заявок с таким статусом пока нет."
        )
        return

    for ticket in tickets:
        keyboard = None

        if ticket.status == "new":
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="✅ Взять в работу",
                        callback_data=f"admin:take:{ticket.id}"
                    )
                ]]
            )

        elif ticket.status == "in_progress":
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="🔒 Закрыть заявку",
                        callback_data=f"admin:close:{ticket.id}"
                    )
                ]]
            )

        await message.answer(
            format_ticket(ticket),
            reply_markup=keyboard
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

    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return

        logger.exception(
            "Ошибка обновления сообщения заявки"
        )

STATUS_NAMES = {
    "new": "🆕 Новая",
    "in_progress": "🔄 В работе",
    "closed": "✅ Закрыта",
}


def format_ticket(ticket) -> str:
    return (
        f"📋 Заявка №{ticket.id}\n"
        f"Название: {ticket.title}\n"
        f"Категория: {ticket.category}\n"
        f"Описание: {ticket.description}\n"
        f"Автор: {ticket.user.full_name}\n"
        f"Статус: {STATUS_NAMES.get(ticket.status, ticket.status)}"
    )

@router.callback_query(F.data.startswith("admin:take:"))
async def admin_take_ticket(
    callback: CallbackQuery,
    state: FSMContext
):

    if not await is_admin(callback.from_user.id):
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    if await state.get_state() != AdminState.active.state:
        await callback.answer(
            "Сначала войдите в режим администратора через /admin",
            show_alert=True
        )
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
        user_id = await take_ticket(ticket_id)

    except SQLAlchemyError:
        await callback.answer(
            "Ошибка при обновлении заявки",
            show_alert=True
        )
        return

    if user_id is None:
        await callback.answer(
            "Заявка уже взята в работу или не существует",
            show_alert=True
        )
        return

    await update_ticket_message(
        callback,
        old_status="new",
        new_status="🔄 В работе"
    )

    await callback.answer()
    try:
        telegram_id = await get_telegram_id(user_id)

        if telegram_id is not None:
            await callback.bot.send_message(
                chat_id=telegram_id,
                text=(
                    f"🔄 Ваша заявка №{ticket_id} "
                    f"взята в работу."
                )
            )

    except (SQLAlchemyError, TelegramAPIError):
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
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    if await state.get_state() != AdminState.active.state:
        await callback.answer(
            "Сначала войдите в режим администратора через /admin",
            show_alert=True
        )
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
        user_id = await close_ticket(ticket_id)

    except SQLAlchemyError:
        await callback.answer(
            "Ошибка при закрытии заявки",
            show_alert=True
        )
        return

    if user_id is None:
        await callback.answer(
            "Заявка уже закрыта или не находится в работе",
            show_alert=True
        )
        return

    await update_ticket_message(
        callback,
        old_status="new",
        new_status="🔄 В работе"
    )

    await callback.answer()

    try:
        telegram_id = await get_telegram_id(user_id)

        if telegram_id is not None:
            await callback.bot.send_message(
                chat_id=telegram_id,
                text=(
                    f"✅ Ваша заявка №{ticket_id} закрыта.\n"
                    "Спасибо за обращение!"
                )
            )

    except (SQLAlchemyError, TelegramAPIError):
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