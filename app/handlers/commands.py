from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import avatar_selection_keyboard
from app.keyboards.reply import BTN_CHANGE, BTN_FACTS, BTN_HISTORY, BTN_RESET, remove_keyboard
from app.services.memory import clear_short_term_history, get_long_term_facts, get_short_term_history
from app.services.user import get_all_avatars, get_or_create_user
from app.states.user import UserState

router = Router()


def _require_avatar(user) -> str | None:
    """Return an error message if user has no avatar selected, else None."""
    if not user.current_avatar_id:
        return "Ты ещё не выбрал(а) аватара. Нажми /start для выбора."
    return None


# --- History (button + command) ---


@router.message(Command("history"))
@router.message(F.text == BTN_HISTORY)
async def cmd_history(message: Message, session: AsyncSession) -> None:
    """Show last 10 messages from current dialog."""
    user = await get_or_create_user(session, message.from_user.id)
    err = _require_avatar(user)
    if err:
        await message.answer(err)
        return

    history = await get_short_term_history(session, user.id, user.current_avatar_id, limit=10)

    if not history:
        await message.answer("В этом диалоге пока нет сообщений. Напиши что-нибудь!")
        return

    lines = []
    for msg in history:
        prefix = "Ты" if msg["role"] == "user" else user.current_avatar.name
        text = msg["content"][:200]
        if len(msg["content"]) > 200:
            text += "..."
        lines.append(f"**{prefix}:** {text}")

    await message.answer(
        "📜 **Последние сообщения:**\n\n" + "\n\n".join(lines),
        parse_mode="Markdown",
    )


# --- Facts (button + command) ---


@router.message(Command("facts"))
@router.message(F.text == BTN_FACTS)
async def cmd_facts(message: Message, session: AsyncSession) -> None:
    """Show all long-term facts stored for current avatar."""
    user = await get_or_create_user(session, message.from_user.id)
    err = _require_avatar(user)
    if err:
        await message.answer(err)
        return

    facts = await get_long_term_facts(session, user.id, user.current_avatar_id)

    if not facts:
        await message.answer(
            "🧠 Пока фактов нет. Продолжай общаться — я начну запоминать!"
        )
        return

    facts_text = "\n".join(f"• {f}" for f in facts)
    await message.answer(
        f"🧠 **Что я помню о тебе** (с {user.current_avatar.name}):\n\n{facts_text}",
        parse_mode="Markdown",
    )


# --- Reset (button + command) ---


@router.message(Command("reset"))
@router.message(F.text == BTN_RESET)
async def cmd_reset(message: Message, session: AsyncSession) -> None:
    """Clear short-term history but keep long-term facts."""
    user = await get_or_create_user(session, message.from_user.id)
    err = _require_avatar(user)
    if err:
        await message.answer(err)
        return

    count = await clear_short_term_history(session, user.id, user.current_avatar_id)
    await message.answer(
        f"🔄 Диалог сброшен! Удалено сообщений: {count}.\n"
        "Долгосрочные факты сохранены — я тебя всё ещё помню."
    )


# --- Change avatar (button + command) ---


@router.message(Command("change_avatar"))
@router.message(F.text == BTN_CHANGE)
async def cmd_change_avatar(
    message: Message, session: AsyncSession, state: FSMContext
) -> None:
    """Return to avatar selection."""
    avatars = await get_all_avatars(session)
    await message.answer(
        "Выбери нового аватара:",
        reply_markup=remove_keyboard(),
    )
    await message.answer(
        "Нажми на персонажа:",
        reply_markup=avatar_selection_keyboard(avatars),
    )
    await state.set_state(UserState.selecting_avatar)
