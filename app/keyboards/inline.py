from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.models import Avatar


class AvatarCallback(CallbackData, prefix="avatar"):
    avatar_id: int


def avatar_selection_keyboard(avatars: list[Avatar]) -> InlineKeyboardMarkup:
    """Build an inline keyboard with one button per avatar."""
    builder = InlineKeyboardBuilder()
    for avatar in avatars:
        builder.button(
            text=avatar.name,
            callback_data=AvatarCallback(avatar_id=avatar.id),
        )
    builder.adjust(1)
    return builder.as_markup()
