# Deployment Guide

## Server Requirements

- Linux (Ubuntu 22.04+ recommended)
- Python 3.10+
- SSH access

## Quick Deploy

```bash
# From project root on your local machine:
bash deploy/deploy.sh
```

The script will:
1. Sync code via rsync (excluding .env, data/, dot-dirs)
2. Create Python venv and install dependencies
3. Set up systemd service
4. Start the bot

## First-Time Server Setup

### 1. Create .env on server

```bash
ssh root@157.22.180.179
nano /opt/avatar-bot/.env
```

Contents:
```
BOT_TOKEN=your_bot_token
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=google/gemini-2.5-flash-lite
DATABASE_URL=sqlite+aiosqlite:///./data/bot.db
```

### 2. Create data directory

```bash
mkdir -p /opt/avatar-bot/data
```

### 3. Deploy

```bash
bash deploy/deploy.sh
```

## Managing the Bot

```bash
# Check status
ssh root@157.22.180.179 "systemctl status avatar-bot"

# View logs
ssh root@157.22.180.179 "journalctl -u avatar-bot -f"

# Restart
ssh root@157.22.180.179 "systemctl restart avatar-bot"

# Stop
ssh root@157.22.180.179 "systemctl stop avatar-bot"
```

## Updating

Just run `deploy/deploy.sh` again. It syncs code and restarts the service.
The SQLite database in `data/` is preserved between deploys.

## Rollback

The deploy script uses rsync with `--delete`, so the server always mirrors
the local codebase. To rollback, checkout the previous git commit locally
and re-run `deploy/deploy.sh`.
