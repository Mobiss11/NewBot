import asyncio

from loguru import logger
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.engine import async_session
from app.db.models import Avatar, MemoryFact, Message
from app.services.llm import extract_facts_from_conversation


async def save_message(
    session: AsyncSession,
    user_id: int,
    avatar_id: int,
    role: str,
    content: str,
) -> Message:
    """Save a message to the database."""
    msg = Message(
        user_id=user_id,
        avatar_id=avatar_id,
        role=role,
        content=content,
    )
    session.add(msg)
    await session.commit()
    return msg


async def get_short_term_history(
    session: AsyncSession,
    user_id: int,
    avatar_id: int,
    limit: int | None = None,
) -> list[dict[str, str]]:
    """Return last N messages as [{"role": ..., "content": ...}], oldest first."""
    if limit is None:
        limit = settings.short_term_limit

    stmt = (
        select(Message)
        .where(Message.user_id == user_id, Message.avatar_id == avatar_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in reversed(messages)]


async def get_long_term_facts(
    session: AsyncSession,
    user_id: int,
    avatar_id: int,
) -> list[str]:
    """Return all stored facts for a user-avatar pair."""
    stmt = (
        select(MemoryFact)
        .where(MemoryFact.user_id == user_id, MemoryFact.avatar_id == avatar_id)
        .order_by(MemoryFact.created_at.asc())
    )
    result = await session.execute(stmt)
    return [f.fact_text for f in result.scalars().all()]


async def get_message_count(
    session: AsyncSession,
    user_id: int,
    avatar_id: int,
) -> int:
    """Count total messages for a user-avatar pair."""
    stmt = (
        select(func.count())
        .select_from(Message)
        .where(Message.user_id == user_id, Message.avatar_id == avatar_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


def build_system_prompt(avatar: Avatar, facts: list[str]) -> str:
    """Assemble the full system prompt with avatar personality + long-term facts."""
    base = avatar.system_prompt
    if facts:
        facts_block = "\n".join(f"- {f}" for f in facts)
        base += (
            "\n\n[LONG-TERM MEMORY — things you remember about this person]\n"
            f"{facts_block}\n"
            "Use these facts naturally in conversation. Do not list them back unless asked."
        )
    return base


async def maybe_extract_facts(
    user_id: int,
    avatar_id: int,
) -> None:
    """Background task: extract facts if message count is a multiple of the interval."""
    try:
        async with async_session() as session:
            count = await get_message_count(session, user_id, avatar_id)

            if count == 0 or count % settings.fact_extraction_interval != 0:
                return

            logger.info(
                f"Extracting facts for user={user_id}, avatar={avatar_id} "
                f"(message count={count})"
            )

            history = await get_short_term_history(
                session, user_id, avatar_id, limit=settings.fact_extraction_interval * 2
            )
            existing_facts = await get_long_term_facts(session, user_id, avatar_id)

            new_facts = await extract_facts_from_conversation(history, existing_facts)

            if not new_facts:
                logger.info(
                    f"No new facts extracted for user={user_id}, avatar={avatar_id}"
                )
                return

            for fact_text in new_facts:
                session.add(
                    MemoryFact(
                        user_id=user_id,
                        avatar_id=avatar_id,
                        fact_text=fact_text,
                    )
                )

            await session.commit()
            logger.info(f"Saved {len(new_facts)} new facts for user={user_id}")

            # Enforce max facts limit
            await _trim_old_facts(session, user_id, avatar_id)

    except Exception as exc:
        logger.error(f"Fact extraction failed: {exc}")


async def _trim_old_facts(
    session: AsyncSession,
    user_id: int,
    avatar_id: int,
) -> None:
    """Remove oldest facts if total exceeds the limit."""
    stmt = (
        select(MemoryFact.id)
        .where(MemoryFact.user_id == user_id, MemoryFact.avatar_id == avatar_id)
        .order_by(MemoryFact.created_at.desc())
        .offset(settings.max_facts_per_avatar)
    )
    result = await session.execute(stmt)
    old_ids = [row[0] for row in result.all()]

    if old_ids:
        await session.execute(
            delete(MemoryFact).where(MemoryFact.id.in_(old_ids))
        )
        await session.commit()
        logger.info(f"Trimmed {len(old_ids)} old facts for user={user_id}")


async def clear_short_term_history(
    session: AsyncSession,
    user_id: int,
    avatar_id: int,
) -> int:
    """Delete all messages for a user-avatar pair. Returns count deleted."""
    count = await get_message_count(session, user_id, avatar_id)
    await session.execute(
        delete(Message).where(
            Message.user_id == user_id, Message.avatar_id == avatar_id
        )
    )
    await session.commit()
    return count


def schedule_fact_extraction(user_id: int, avatar_id: int) -> None:
    """Fire-and-forget background task for fact extraction."""
    asyncio.create_task(maybe_extract_facts(user_id, avatar_id))
