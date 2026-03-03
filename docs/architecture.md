# Обзор архитектуры

## Поток данных

```
User Message
    │
    ▼
┌─────────────────┐
│  Aiogram Router  │  (handlers/chat.py)
│  FSM: chatting   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  Memory Service  │────▶│  Database (SQLite)│
│  (services/      │     │  - messages       │
│   memory.py)     │◀────│  - memory_facts   │
└────────┬────────┘     └──────────────────┘
         │
         │  Build system prompt:
         │  avatar.system_prompt + facts + history
         ▼
┌─────────────────┐     ┌──────────────────┐
│   LLM Service    │────▶│  OpenRouter API   │
│  (services/      │     │  (Gemini 2.5      │
│   llm.py)        │◀────│   Flash Lite)     │
└────────┬────────┘     └──────────────────┘
         │
         │  Streaming chunks
         ▼
┌─────────────────┐
│  Telegram Edit   │  (edit_message_text every 1s)
│  Message         │
└─────────────────┘
         │
         │  After complete response:
         ▼
┌─────────────────┐
│  Background Task │  (every 5 messages)
│  Fact Extraction │  → saves to memory_facts
└─────────────────┘
```

## Структура модулей

```
app/
├── main.py           # Entry point, dispatcher wiring
├── config.py         # Settings from .env (pydantic-settings)
├── db/
│   ├── engine.py     # SQLAlchemy async engine + session factory
│   ├── models.py     # ORM: User, Avatar, Message, MemoryFact
│   └── seed.py       # Pre-populate 3 avatars on startup
├── services/
│   ├── user.py       # User CRUD, avatar assignment
│   ├── llm.py        # OpenRouter streaming client + fact extraction
│   └── memory.py     # Short-term history, long-term facts, prompt builder
├── handlers/
│   ├── start.py      # /start command, avatar selection callback
│   ├── chat.py       # Main message handler with streaming
│   └── commands.py   # /history, /facts, /reset, /change_avatar
├── keyboards/
│   ├── inline.py     # Avatar selection keyboard + CallbackData
│   └── reply.py      # Persistent reply keyboard
├── middlewares/
│   └── db_session.py # Inject AsyncSession into every handler
├── states/
│   └── user.py       # FSM: selecting_avatar → chatting
└── utils/
    └── text.py       # Text truncation helper
```

## Схема базы данных

| Table | Columns | Назначение |
|-------|---------|------------|
| `users` | id, telegram_id, current_avatar_id, created_at | Профили пользователей |
| `avatars` | id, name, description, system_prompt | Определения AI-персонажей |
| `messages` | id, user_id, avatar_id, role, content, created_at | История диалогов |
| `memory_facts` | id, user_id, avatar_id, fact_text, created_at | Извлечённые факты долгосрочной памяти |

## Состояния FSM

1. **selecting_avatar** — Пользователь видит инлайн-клавиатуру и выбирает аватар. Бот ожидает нажатия на кнопку с персонажем.
2. **chatting** — Пользователь отправляет сообщения, бот стримит ответы от AI. Основной рабочий режим диалога.
