# AI Avatar Chatbot

Telegram bot with AI personalities. Users choose a character (avatar) and chat with it. The bot remembers conversation context (short-term memory) and extracts personal facts for long-term recall.

## Features

- **3 unique AI avatars**: Marcus (Stoic philosopher), ZARA-7 (rogue AI from 2187), Baba Klava (Russian grandma)
- **Streaming responses**: Messages appear progressively, ChatGPT-style
- **Two-level memory system**:
  - Short-term: last 10 messages as conversation context
  - Long-term: extracted facts persist across sessions and resets
- **Commands**: `/start`, `/history`, `/facts`, `/reset`, `/change_avatar`

## Tech Stack

- Python 3.10+
- [Aiogram 3.x](https://docs.aiogram.dev/) — Telegram Bot framework
- [OpenRouter](https://openrouter.ai/) — LLM API (Gemini 2.5 Flash Lite)
- SQLite + aiosqlite — async database
- SQLAlchemy 2.0 — async ORM
- pydantic-settings — configuration management

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/Mobiss11/NewBot.git
cd NewBot
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your tokens:
#   BOT_TOKEN=your_telegram_bot_token
#   OPENROUTER_API_KEY=your_openrouter_key
```

### 3. Run

```bash
python -m app.main
```

The bot will:
- Create SQLite database in `data/bot.db`
- Seed 3 avatar characters
- Start polling for Telegram updates

### 4. Use

1. Open your bot in Telegram
2. Send `/start`
3. Choose an avatar
4. Start chatting!

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + avatar selection |
| `/history` | Show last 10 messages |
| `/facts` | Show all remembered facts |
| `/reset` | Clear dialog history (keeps facts) |
| `/change_avatar` | Switch to a different avatar |

## Project Structure

```
app/
├── main.py           # Entry point
├── config.py         # Settings from .env
├── db/
│   ├── engine.py     # SQLAlchemy async engine
│   ├── models.py     # ORM models (User, Avatar, Message, MemoryFact)
│   └── seed.py       # Avatar data seeding
├── services/
│   ├── user.py       # User CRUD
│   ├── llm.py        # OpenRouter streaming + fact extraction
│   └── memory.py     # Memory system (short-term + long-term)
├── handlers/
│   ├── start.py      # /start + avatar selection
│   ├── chat.py       # Main chat with streaming
│   └── commands.py   # /history, /facts, /reset, /change_avatar
├── keyboards/
│   └── inline.py     # Inline keyboard builder
├── middlewares/
│   └── db_session.py # DB session injection
└── states/
    └── user.py       # FSM states
```

## Memory System

See [docs/memory-system.md](docs/memory-system.md) for detailed documentation.

**Short-term**: Last 10 messages stored in DB, sent as LLM history.

**Long-term**: Every 5 messages, a background LLM call extracts personal facts (name, interests, etc.) and saves them. Facts are injected into the system prompt on every request, so the avatar "remembers" the user.

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Handlers](docs/handlers.md)
- [Services](docs/services.md)
- [Memory System](docs/memory-system.md)
- [Streaming](docs/streaming.md)
- [Deployment](docs/deploy.md)

## Deployment

```bash
bash deploy/deploy.sh
```

See [docs/deploy.md](docs/deploy.md) for full deployment guide.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | Yes | — | Telegram Bot API token |
| `OPENROUTER_API_KEY` | Yes | — | OpenRouter API key |
| `OPENROUTER_MODEL` | No | google/gemini-2.5-flash-lite | LLM model |
| `DATABASE_URL` | No | sqlite+aiosqlite:///./data/bot.db | Database connection |
| `SHORT_TERM_LIMIT` | No | 10 | Messages in short-term memory |
| `FACT_EXTRACTION_INTERVAL` | No | 5 | Messages between fact extractions |
| `MAX_FACTS_PER_AVATAR` | No | 20 | Max stored facts per user-avatar |
