from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Avatar, User


async def get_or_create_user(session: AsyncSession, telegram_id: int) -> User:
    """Get existing user or create a new one."""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user


async def set_user_avatar(session: AsyncSession, telegram_id: int, avatar_id: int) -> User:
    """Assign an avatar to a user."""
    user = await get_or_create_user(session, telegram_id)
    user.current_avatar_id = avatar_id
    await session.commit()
    await session.refresh(user)
    return user


async def get_all_avatars(session: AsyncSession) -> list[Avatar]:
    """Fetch all available avatars."""
    result = await session.execute(select(Avatar))
    return list(result.scalars().all())


async def get_avatar_by_id(session: AsyncSession, avatar_id: int) -> Avatar | None:
    """Fetch a single avatar by ID."""
    result = await session.execute(select(Avatar).where(Avatar.id == avatar_id))
    return result.scalar_one_or_none()
