# Документация сервисов

## user.py — Управление пользователями

### `get_or_create_user(session, telegram_id) -> User`
Находит пользователя по Telegram ID или создаёт нового. Идемпотентная операция.

### `set_user_avatar(session, telegram_id, avatar_id) -> User`
Назначает аватар пользователю. Обновляет поле `current_avatar_id`.

### `get_all_avatars(session) -> list[Avatar]`
Возвращает все доступные аватары из базы данных.

### `get_avatar_by_id(session, avatar_id) -> Avatar | None`
Возвращает один аватар по первичному ключу.

## llm.py — Интеграция с LLM

Использует OpenAI SDK, направленный на OpenRouter (`https://openrouter.ai/api/v1`).

### `stream_chat_response(messages) -> AsyncIterator[str]`
Отправляет сообщения в LLM и возвращает текстовые чанки по мере их поступления.
Используется для потоковой отправки ответов в Telegram.

### `extract_facts_from_conversation(conversation, existing_facts) -> list[str]`
Выполняет отдельный (не потоковый) вызов LLM с промптом для извлечения фактов.
Возвращает список новых фактов в виде строк, распарсенных из JSON-ответа.

**Надёжность**: Обрабатывает markdown code fences в ответе, невалидный JSON
и ошибки API — при любой ошибке возвращает пустой список.

## memory.py — Система памяти

### `save_message(session, user_id, avatar_id, role, content) -> Message`
Сохраняет сообщение (от пользователя или ассистента) в базу данных.

### `get_short_term_history(session, user_id, avatar_id, limit) -> list[dict]`
Возвращает последние N сообщений в формате `[{"role": "user"|"assistant", "content": "..."}]`.
Отсортированы от старых к новым для контекста LLM.

### `get_long_term_facts(session, user_id, avatar_id) -> list[str]`
Возвращает все сохранённые факты для пары пользователь-аватар.

### `build_system_prompt(avatar, facts) -> str`
Собирает полный системный промпт: личность аватара + блок долгосрочной памяти.

### `schedule_fact_extraction(user_id, avatar_id)`
Fire-and-forget: создаёт `asyncio.Task`, который проверяет, нужно ли запустить
извлечение фактов (каждые 5 сообщений), и выполняет его при необходимости.

### `clear_short_term_history(session, user_id, avatar_id) -> int`
Удаляет все сообщения для пары пользователь-аватар. Возвращает количество удалённых.
