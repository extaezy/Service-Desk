import logging
import httpx
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter

from app.keyboards.categories import category_keyboard
from app.keyboards.main_menu import main_keyboard
from app.keyboards.cancel import cancel_keyboard
from app.states.ticket import TicketForm
from app.keyboards.confirm import confirm_keyboard

from app.api_client.tickets import create_ticket

router = Router()
logger = logging.getLogger(__name__)

@router.message(
    StateFilter(None),
    F.text == "Создать заявку"
)
async def start_ticket_creation(message: Message, state: FSMContext):
    await state.set_state(TicketForm.title)
    await message.answer(
        "Введите название заявки:",
        reply_markup=cancel_keyboard
    )


@router.message(F.text == "❌ Отменить создание")
async def cancel_handler(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    for key in ("category_message_id", "confirm_message_id"):
        message_id = data.get(key)

        if message_id is not None:
            try:
                await message.bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=message_id,
                    reply_markup=None
                )
            except TelegramBadRequest as error:
                logger.warning(
                    "Не удалось удалить клавиатуру сообщения %s: %s",
                    message_id,
                    error
                )

    await state.clear()

    await message.answer(
        "Создание заявки отменено.",
        reply_markup=main_keyboard
    )

@router.message(F.text == "⬅️ Назад")
async def back_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()

    if current_state == TicketForm.title.state:
        await state.clear()

        await message.answer(
            "Главное меню:",
            reply_markup=main_keyboard
        )

    elif current_state == TicketForm.category.state:
        message_id = data.get("category_message_id")

        if message_id is not None:
            try:
                await message.bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=message_id,
                    reply_markup=None
                )
            except TelegramBadRequest as error:
                logger.warning(
                    "Не удалось удалить клавиатуру %s: %s",
                    message_id,
                    error
                )

        await state.update_data(category_message_id=None)
        await state.set_state(TicketForm.title)

        await message.answer(
            "Введите название заявки:",
            reply_markup=cancel_keyboard
        )

    elif current_state == TicketForm.description.state:
        await state.set_state(TicketForm.category)

        sent_message = await message.answer(
            "Выберите категорию заявки:",
            reply_markup=category_keyboard
        )

        await state.update_data(
            category_message_id=sent_message.message_id
        )

        await message.answer(
            "Для возврата или отмены используйте кнопки ниже.",
            reply_markup=cancel_keyboard
        )

    elif current_state == TicketForm.confirm.state:
        message_id = data.get("confirm_message_id")

        if message_id is not None:
            try:
                await message.bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=message_id,
                    reply_markup=None
                )
            except TelegramBadRequest as error:
                logger.warning(
                    "Не удалось удалить клавиатуру %s: %s",
                    message_id,
                    error
                )

        await state.update_data(confirm_message_id=None)
        await state.set_state(TicketForm.description)

        await message.answer(
            "Подробно опишите проблему:",
            reply_markup=cancel_keyboard
        )

@router.message(TicketForm.title)
async def process_title(message: Message, state: FSMContext):

    if not message.text or not message.text.strip():
        await message.answer(
            "Пожалуйста, введите название заявки текстовым сообщением."
        )
        return

    title = message.text.strip()

    if len(title) > 100:
        await message.answer(
            "Название слишком длинное, попробуйте ещё раз."
        )
        return

    await state.update_data(title=title)
    await state.set_state(TicketForm.category)

    sent_message = await message.answer(
        "Выберите категорию заявки:",
        reply_markup=category_keyboard
    )
    await message.answer(
        "Для возврата или отмены используйте кнопки ниже.",
        reply_markup=cancel_keyboard
    )
    await state.update_data(
        category_message_id=sent_message.message_id
    )


@router.callback_query(
    TicketForm.category,
    F.data.startswith("category:")
)
async def process_category(
    callback: CallbackQuery,
    state: FSMContext
):
    categories = {
        "hardware": "Оборудование",
        "software": "Программное обеспечение",
        "network": "Сеть и интернет",
        "other": "Другое",
    }

    category_id = callback.data.split(":")[1]
    category = categories.get(category_id)
    if category is None:
        await callback.answer(
            "Неизвестная ошибка, попробуйте ещё раз",
            show_alert=True
        )
        return


    await state.update_data(category=category_id)
    await state.set_state(TicketForm.description)

    await callback.answer()

    await callback.message.edit_text(
        f"Выбрана категория: {category}"
    )
    await state.update_data(category_message_id=None)

    await callback.message.answer(
        "Подробно опишите проблему:",
        reply_markup=cancel_keyboard
    )


@router.message(TicketForm.description)
async def process_description(
    message: Message,
    state: FSMContext
):
    if not message.text or not message.text.strip():
        await message.answer(
            "Опишите проблему текстовым сообщением."
        )
        return

    description = message.text.strip()

    if len(description) > 400:
        await message.answer(
            "Описание слишком длинное."
            "Сократите и попробуйте ещё раз."
        )
        return

    await state.update_data(description=description)
    data = await state.get_data()

    await state.set_state(TicketForm.confirm)

    sent_message = await message.answer(
        f"Проверьте вашу заявку:\n\n"
        f"Название: {data['title']}\n"
        f"Категория: {data['category']}\n"
        f"Описание: {data['description']}",
        reply_markup=confirm_keyboard
    )

    await state.update_data(
        confirm_message_id=sent_message.message_id
    )

    await message.answer(
        "Для исправления или отмены используйте кнопки ниже.",
        reply_markup=cancel_keyboard
    )


@router.callback_query(
    TicketForm.confirm,
    F.data == "ticket:confirm"
)
async def confirm_ticket(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()

    try:
        ticket = await create_ticket(
            telegram_user_id=callback.from_user.id,
            title=data["title"],
            category=data["category"],
            description=data["description"],
        )

    except (httpx.HTTPStatusError, httpx.RequestError):
        logger.exception(
            "Ошибка при сохранении заявки пользователя %s",
            callback.from_user.id,
        )

        await callback.answer(
            "Не удалось сохранить заявку",
            show_alert=True,
        )
        return

    await state.clear()
    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except TelegramBadRequest:
        logger.exception(
            "Не удалось убрать кнопку заявки №%s",
            ticket['id']
        )

    await callback.answer()

    await callback.message.answer(
        f"✅ Заявка №{ticket['id']} успешно создана."
    )

    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_keyboard
    )


@router.callback_query(
    TicketForm.confirm,
    F.data == "ticket:cancel"
)
async def reject_ticket(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.clear()
    await callback.answer()

    await callback.message.edit_text(
        "❌ Создание заявки отменено."
    )

    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_keyboard
    )