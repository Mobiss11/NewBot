# AI Avatar Chatbot

## About
Telegram bot with AI avatars. Users pick a character and chat via OpenRouter LLM.
Two-level memory: short-term (last 10 messages) and long-term (extracted facts).

## Stack
- Bot: aiogram 3.x, Python 3.10+
- LLM: OpenRouter API (google/gemini-2.5-flash-lite)
- DB: SQLite + aiosqlite + SQLAlchemy 2.0 async
- Config: pydantic-settings (.env)

## Structure
- `app/handlers/` — bot command and message handlers
- `app/services/` — LLM client, memory logic, user CRUD
- `app/db/` — models, engine, seed data
- `app/middlewares/` — DB session injection
- `app/states/` — FSM states (selecting_avatar, chatting)
- `app/keyboards/` — inline keyboard builders

## Key Files
- `app/services/memory.py` — core memory system (short-term + long-term)
- `app/services/llm.py` — OpenRouter streaming + fact extraction
- `app/handlers/chat.py` — main chat handler with streaming
- `app/db/models.py` — 4 ORM models: User, Avatar, Message, MemoryFact
- `app/db/seed.py` — 3 avatar definitions with system prompts

## Commands
```bash
# Run bot
python -m app.main

# Deploy to server
bash deploy/deploy.sh
```

## Documentation
- Architecture: [docs/architecture.md](docs/architecture.md)
- Handlers: [docs/handlers.md](docs/handlers.md)
- Services: [docs/services.md](docs/services.md)
- Memory System: [docs/memory-system.md](docs/memory-system.md)
- Streaming: [docs/streaming.md](docs/streaming.md)
- Deployment: [docs/deploy.md](docs/deploy.md)

## AI Rules
- Respond in Russian, code/comments in English
- Async everywhere, type hints required
- SQLAlchemy 2.0: Mapped[], select(), async sessions
- loguru for logging, never print()
- Conventional commits: feat: fix: refactor:
