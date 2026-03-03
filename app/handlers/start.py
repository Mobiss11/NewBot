from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import AvatarCallback, avatar_selection_keyboard
from app.keyboards.reply import chat_keyboard, remove_keyboard
from app.services.user import get_all_avatars, get_avatar_by_id, get_or_create_user, set_user_avatar
from app.states.user import UserState

router = Router()

WELCOME_TEXT = (
    "Привет! Я бот с ИИ-персонажами.\n\n"
    "Выбери себе собеседника — у каждого свой характер, "
    "и он будет запоминать факты о тебе между диалогами.\n\n"
    "Выбирай:"
)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    """Show welcome message and avatar selection keyboard."""
    await get_or_create_user(session, message.from_user.id)
    avatars = await get_all_avatars(session)

    await message.answer(
        WELCOME_TEXT,
        reply_markup=remove_keyboard(),
    )
    await message.answer(
        "Нажми на персонажа:",
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
        await callback.answer("Аватар не найден, попробуй ещё раз.")
        return

    await set_user_avatar(session, callback.from_user.id, avatar.id)
    await state.set_state(UserState.chatting)

    await callback.message.edit_text(
        f"✅ Ты выбрал(а) **{avatar.name}**!\n"
        f"_{avatar.description}_",
        parse_mode="Markdown",
    )

    # Show reply keyboard with action buttons
    await callback.message.answer(
        "Напиши мне что-нибудь, чтобы начать общение 👇",
        reply_markup=chat_keyboard(),
    )
    await callback.answer()
