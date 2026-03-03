from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

BTN_HISTORY = "📜 История"
BTN_FACTS = "🧠 Факты обо мне"
BTN_RESET = "🔄 Сбросить диалог"
BTN_CHANGE = "👤 Сменить аватара"

ALL_BUTTONS = {BTN_HISTORY, BTN_FACTS, BTN_RESET, BTN_CHANGE}


def chat_keyboard() -> ReplyKeyboardMarkup:
    """Persistent reply keyboard shown during chatting."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_HISTORY), KeyboardButton(text=BTN_FACTS)],
            [KeyboardButton(text=BTN_RESET), KeyboardButton(text=BTN_CHANGE)],
        ],
        resize_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
