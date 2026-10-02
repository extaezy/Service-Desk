from aiogram.fsm.state import State, StatesGroup


class TicketForm(StatesGroup):
    title = State()
    category = State()
    description = State()
    confirm = State()