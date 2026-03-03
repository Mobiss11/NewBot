"""Test database models and seed data."""
import pytest
from sqlalchemy import select

from app.db.models import Avatar, MemoryFact, Message, User
from app.db.seed import seed_avatars


@pytest.mark.asyncio
async def test_seed_avatars_creates_three(session):
    """Seed should create exactly 3 avatars."""
    await seed_avatars(session)

    result = await session.execute(select(Avatar))
    avatars = result.scalars().all()
    assert len(avatars) == 3


@pytest.mark.asyncio
async def test_seed_avatars_idempotent(session):
    """Running seed twice should not duplicate avatars."""
    await seed_avatars(session)
    await seed_avatars(session)

    result = await session.execute(select(Avatar))
    avatars = result.scalars().all()
    assert len(avatars) == 3


@pytest.mark.asyncio
async def test_avatars_have_required_fields(seeded_session):
    """Each avatar should have name, description, system_prompt."""
    result = await seeded_session.execute(select(Avatar))
    for avatar in result.scalars().all():
        assert avatar.name
        assert avatar.description
        assert avatar.system_prompt
        assert len(avatar.system_prompt) > 50


@pytest.mark.asyncio
async def test_create_user(session):
    """User can be created with telegram_id."""
    user = User(telegram_id=123456789)
    session.add(user)
    await session.commit()

    result = await session.execute(select(User).where(User.telegram_id == 123456789))
    found = result.scalar_one()
    assert found.telegram_id == 123456789
    assert found.current_avatar_id is None


@pytest.mark.asyncio
async def test_create_message(seeded_session):
    """Messages can be created and linked to user+avatar."""
    user = User(telegram_id=111)
    seeded_session.add(user)
    await seeded_session.commit()

    result = await seeded_session.execute(select(Avatar).limit(1))
    avatar = result.scalar_one()

    msg = Message(user_id=user.id, avatar_id=avatar.id, role="user", content="Hello!")
    seeded_session.add(msg)
    await seeded_session.commit()

    result = await seeded_session.execute(select(Message).where(Message.user_id == user.id))
    found = result.scalar_one()
    assert found.content == "Hello!"
    assert found.role == "user"


@pytest.mark.asyncio
async def test_create_memory_fact(seeded_session):
    """Memory facts can be created and linked to user+avatar."""
    user = User(telegram_id=222)
    seeded_session.add(user)
    await seeded_session.commit()

    result = await seeded_session.execute(select(Avatar).limit(1))
    avatar = result.scalar_one()

    fact = MemoryFact(user_id=user.id, avatar_id=avatar.id, fact_text="User likes Python")
    seeded_session.add(fact)
    await seeded_session.commit()

    result = await seeded_session.execute(
        select(MemoryFact).where(MemoryFact.user_id == user.id)
    )
    found = result.scalar_one()
    assert found.fact_text == "User likes Python"
