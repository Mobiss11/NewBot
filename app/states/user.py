from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    selecting_avatar = State()
    chatting = State()
