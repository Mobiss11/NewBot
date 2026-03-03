import time

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.keyboards.reply import ALL_BUTTONS
from app.services.llm import stream_chat_response
from app.services.memory import (
    build_system_prompt,
    get_long_term_facts,
    get_short_term_history,
    save_message,
    schedule_fact_extraction,
)
from app.services.user import get_or_create_user
from app.states.user import UserState

router = Router()


@router.message(UserState.chatting, F.text)
async def handle_chat_message(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Process a user message: build context, stream LLM response, save to DB."""
    # Skip button presses — they're handled by commands router
    if message.text in ALL_BUTTONS:
        return

    user = await get_or_create_user(session, message.from_user.id)

    if not user.current_avatar_id or not user.current_avatar:
        await message.answer("Сначала выбери аватара: /start")
        return

    avatar = user.current_avatar

    # Save user message
    await save_message(session, user.id, avatar.id, "user", message.text)

    # Build LLM context
    facts = await get_long_term_facts(session, user.id, avatar.id)
    history = await get_short_term_history(session, user.id, avatar.id)
    system_prompt = build_system_prompt(avatar, facts)

    llm_messages = [
        {"role": "system", "content": system_prompt},
        *history,
    ]

    # Send placeholder
    bot_msg = await message.answer("...")

    full_text = ""
    last_edit_time = 0.0

    try:
        async for chunk in stream_chat_response(llm_messages):
            full_text += chunk
            now = time.monotonic()

            if now - last_edit_time >= settings.stream_edit_interval and full_text.strip():
                try:
                    await bot_msg.edit_text(full_text + " ▌")
                    last_edit_time = now
                except TelegramBadRequest:
                    pass

        # Final edit — complete text without cursor
        if full_text.strip():
            try:
                await bot_msg.edit_text(full_text)
            except TelegramBadRequest:
                pass
        else:
            await bot_msg.edit_text("Не удалось сгенерировать ответ. Попробуй ещё раз.")
            return

    except Exception as exc:
        logger.error(f"LLM streaming failed: {exc}")
        try:
            await bot_msg.edit_text(
                "Извини, ИИ-сервис временно недоступен. Попробуй чуть позже."
            )
        except TelegramBadRequest:
            pass
        return

    # Save assistant response
    await save_message(session, user.id, avatar.id, "assistant", full_text)

    # Trigger fact extraction in background
    schedule_fact_extraction(user.id, avatar.id)
