# Services Documentation

## user.py — User Management

### `get_or_create_user(session, telegram_id) -> User`
Finds user by Telegram ID or creates a new one. Idempotent.

### `set_user_avatar(session, telegram_id, avatar_id) -> User`
Assigns an avatar to the user. Updates `current_avatar_id`.

### `get_all_avatars(session) -> list[Avatar]`
Returns all available avatars from DB.

### `get_avatar_by_id(session, avatar_id) -> Avatar | None`
Returns a single avatar by primary key.

## llm.py — LLM Integration

Uses OpenAI SDK pointed at OpenRouter (`https://openrouter.ai/api/v1`).

### `stream_chat_response(messages) -> AsyncIterator[str]`
Sends messages to the LLM and yields text chunks as they arrive.
Used for streaming responses to Telegram.

### `extract_facts_from_conversation(conversation, existing_facts) -> list[str]`
Sends a separate (non-streaming) LLM call with a fact extraction prompt.
Returns a list of new fact strings parsed from JSON response.

**Robustness**: Handles markdown code fences in response, invalid JSON,
and API failures — returns empty list on any error.

## memory.py — Memory System

### `save_message(session, user_id, avatar_id, role, content) -> Message`
Persists a message (user or assistant) to the database.

### `get_short_term_history(session, user_id, avatar_id, limit) -> list[dict]`
Returns last N messages as `[{"role": "user"|"assistant", "content": "..."}]`.
Ordered oldest-first for LLM context.

### `get_long_term_facts(session, user_id, avatar_id) -> list[str]`
Returns all stored facts for a user-avatar pair.

### `build_system_prompt(avatar, facts) -> str`
Assembles the full system prompt: avatar's personality + long-term memory block.

### `schedule_fact_extraction(user_id, avatar_id)`
Fire-and-forget: creates an `asyncio.Task` that checks if fact extraction
should run (every 5 messages) and executes it if needed.

### `clear_short_term_history(session, user_id, avatar_id) -> int`
Deletes all messages for a user-avatar pair. Returns count deleted.
