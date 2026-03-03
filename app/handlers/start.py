from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import AvatarCallback, avatar_selection_keyboard
from app.services.user import get_all_avatars, get_avatar_by_id, get_or_create_user, set_user_avatar
from app.states.user import UserState

router = Router()

WELCOME_TEXT = (
    "Welcome! I'm a bot with AI personalities.\n\n"
    "Choose your companion — each has a unique character "
    "and will remember things about you across conversations.\n\n"
    "Pick one:"
)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Show welcome message and avatar selection keyboard."""
    await get_or_create_user(session, message.from_user.id)
    avatars = await get_all_avatars(session)

    await message.answer(
        WELCOME_TEXT,
        reply_markup=avatar_selection_keyboard(avatars),
    )
    await state.set_state(UserState.selecting_avatar)


@router.callback_query(AvatarCallback.filter(), UserState.selecting_avatar)
async def on_avatar_selected(
    callback: CallbackQuery,
    callback_data: AvatarCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Handle avatar selection, switch to chatting state."""
    avatar = await get_avatar_by_id(session, callback_data.avatar_id)
    if avatar is None:
        await callback.answer("Avatar not found, try again.")
        return

    await set_user_avatar(session, callback.from_user.id, avatar.id)
    await state.set_state(UserState.chatting)

    await callback.message.edit_text(
        f"You chose **{avatar.name}**!\n"
        f"_{avatar.description}_\n\n"
        "Send me a message to start chatting.\n"
        "Commands: /history /facts /reset /change_avatar",
        parse_mode="Markdown",
    )
    await callback.answer()
