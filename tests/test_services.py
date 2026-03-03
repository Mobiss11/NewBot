"""Test service layer: user, memory, llm."""
import json

import pytest
from sqlalchemy import select

from app.db.models import Avatar, MemoryFact, Message, User
from app.services.memory import (
    build_system_prompt,
    clear_short_term_history,
    get_long_term_facts,
    get_message_count,
    get_short_term_history,
    save_message,
)
from app.services.user import get_all_avatars, get_avatar_by_id, get_or_create_user, set_user_avatar


# --- User service ---


@pytest.mark.asyncio
async def test_get_or_create_user_creates(session):
    """First call creates user, second returns the same."""
    user1 = await get_or_create_user(session, 999)
    user2 = await get_or_create_user(session, 999)
    assert user1.id == user2.id
    assert user1.telegram_id == 999


@pytest.mark.asyncio
async def test_set_user_avatar(seeded_session):
    """User avatar can be set."""
    avatars = await get_all_avatars(seeded_session)
    user = await get_or_create_user(seeded_session, 888)

    assert user.current_avatar_id is None

    updated = await set_user_avatar(seeded_session, 888, avatars[0].id)
    assert updated.current_avatar_id == avatars[0].id


@pytest.mark.asyncio
async def test_get_avatar_by_id(seeded_session):
    """Avatar lookup by ID works."""
    avatars = await get_all_avatars(seeded_session)
    found = await get_avatar_by_id(seeded_session, avatars[0].id)
    assert found is not None
    assert found.name == avatars[0].name


@pytest.mark.asyncio
async def test_get_avatar_by_id_not_found(seeded_session):
    """Avatar lookup returns None for non-existent ID."""
    found = await get_avatar_by_id(seeded_session, 9999)
    assert found is None


# --- Memory service ---


@pytest.mark.asyncio
async def test_save_and_get_history(seeded_session):
    """Messages are saved and retrieved in correct order."""
    user = await get_or_create_user(seeded_session, 777)
    avatars = await get_all_avatars(seeded_session)
    avatar = avatars[0]

    await save_message(seeded_session, user.id, avatar.id, "user", "msg1")
    await save_message(seeded_session, user.id, avatar.id, "assistant", "reply1")
    await save_message(seeded_session, user.id, avatar.id, "user", "msg2")

    history = await get_short_term_history(seeded_session, user.id, avatar.id)
    assert len(history) == 3
    # Oldest first
    assert history[0]["content"] == "msg1"
    assert history[0]["role"] == "user"
    assert history[1]["content"] == "reply1"
    assert history[2]["content"] == "msg2"


@pytest.mark.asyncio
async def test_short_term_history_limit(seeded_session):
    """History respects the limit parameter."""
    user = await get_or_create_user(seeded_session, 666)
    avatars = await get_all_avatars(seeded_session)
    avatar = avatars[0]

    for i in range(10):
        await save_message(seeded_session, user.id, avatar.id, "user", f"msg{i}")

    history = await get_short_term_history(seeded_session, user.id, avatar.id, limit=3)
    assert len(history) == 3
    # Should be the last 3 messages
    assert history[0]["content"] == "msg7"
    assert history[2]["content"] == "msg9"


@pytest.mark.asyncio
async def test_get_message_count(seeded_session):
    """Message count is accurate."""
    user = await get_or_create_user(seeded_session, 555)
    avatars = await get_all_avatars(seeded_session)
    avatar = avatars[0]

    assert await get_message_count(seeded_session, user.id, avatar.id) == 0

    await save_message(seeded_session, user.id, avatar.id, "user", "hello")
    assert await get_message_count(seeded_session, user.id, avatar.id) == 1


@pytest.mark.asyncio
async def test_long_term_facts(seeded_session):
    """Facts can be stored and retrieved."""
    user = await get_or_create_user(seeded_session, 444)
    avatars = await get_all_avatars(seeded_session)
    avatar = avatars[0]

    # No facts initially
    facts = await get_long_term_facts(seeded_session, user.id, avatar.id)
    assert facts == []

    # Add facts
    seeded_session.add(MemoryFact(user_id=user.id, avatar_id=avatar.id, fact_text="Likes cats"))
    seeded_session.add(MemoryFact(user_id=user.id, avatar_id=avatar.id, fact_text="Lives in Moscow"))
    await seeded_session.commit()

    facts = await get_long_term_facts(seeded_session, user.id, avatar.id)
    assert len(facts) == 2
    assert "Likes cats" in facts


@pytest.mark.asyncio
async def test_clear_short_term_history(seeded_session):
    """Reset clears messages but not facts."""
    user = await get_or_create_user(seeded_session, 333)
    avatars = await get_all_avatars(seeded_session)
    avatar = avatars[0]

    await save_message(seeded_session, user.id, avatar.id, "user", "hello")
    await save_message(seeded_session, user.id, avatar.id, "assistant", "hi")

    seeded_session.add(MemoryFact(user_id=user.id, avatar_id=avatar.id, fact_text="Test fact"))
    await seeded_session.commit()

    count = await clear_short_term_history(seeded_session, user.id, avatar.id)
    assert count == 2

    # Messages gone
    history = await get_short_term_history(seeded_session, user.id, avatar.id)
    assert history == []

    # Facts still there
    facts = await get_long_term_facts(seeded_session, user.id, avatar.id)
    assert len(facts) == 1
    assert facts[0] == "Test fact"


@pytest.mark.asyncio
async def test_build_system_prompt_without_facts(seeded_session):
    """System prompt without facts is just the avatar prompt."""
    avatars = await get_all_avatars(seeded_session)
    avatar = avatars[0]

    prompt = build_system_prompt(avatar, [])
    assert prompt == avatar.system_prompt


@pytest.mark.asyncio
async def test_build_system_prompt_with_facts(seeded_session):
    """System prompt with facts includes the memory block."""
    avatars = await get_all_avatars(seeded_session)
    avatar = avatars[0]

    prompt = build_system_prompt(avatar, ["User is named Alex", "User likes chess"])
    assert avatar.system_prompt in prompt
    assert "LONG-TERM MEMORY" in prompt
    assert "User is named Alex" in prompt
    assert "User likes chess" in prompt


# --- LLM fact parsing ---


def test_fact_json_parsing():
    """Verify that the expected JSON format can be parsed."""
    raw = '["User is Alex", "User lives in Berlin"]'
    facts = json.loads(raw)
    assert isinstance(facts, list)
    assert len(facts) == 2


def test_fact_json_with_code_fence():
    """Simulate LLM wrapping JSON in markdown code fences."""
    raw = '```json\n["User likes Python"]\n```'
    lines = raw.strip().split("\n")
    inner = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    facts = json.loads(inner.strip())
    assert facts == ["User likes Python"]


def test_empty_facts():
    """Empty array means no new facts."""
    raw = "[]"
    facts = json.loads(raw)
    assert facts == []
