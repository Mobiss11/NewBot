# Руководство по деплою

## Требования к серверу

- Linux (рекомендуется Ubuntu 22.04+)
- Docker и Docker Compose v2
- Доступ по SSH

## Быстрый деплой

```bash
# Из корня проекта на локальной машине:
bash deploy/deploy.sh
```

Скрипт выполнит следующее:
1. Синхронизирует код через rsync (исключая .env, data/, скрытые директории)
2. Соберёт Docker-образ (multi-stage build, python:3.12-slim)
3. Запустит контейнер через `docker compose up -d`

## Docker-архитектура

```
┌─────────────────────────────────┐
│  Docker Container (avatar-bot)  │
│  python:3.12-slim               │
│  USER: appuser (non-root)       │
│  CMD: python -m app.main        │
│                                 │
│  Volume: /app/data → bot-data   │
│  (SQLite БД сохраняется)        │
└─────────────────────────────────┘
```

**Dockerfile** — multi-stage build:
- Stage 1 (builder): устанавливает зависимости в venv
- Stage 2 (runtime): копирует venv и код, запускает под non-root пользователем

**docker-compose.yml**:
- `restart: unless-stopped` — автоперезапуск
- `security_opt: no-new-privileges` — запрет эскалации привилегий
- Named volume `bot-data` для персистентности SQLite

## Первоначальная настройка сервера

### 1. Установите Docker (если нет)

```bash
ssh root@157.22.180.179
apt update && apt install -y docker.io docker-compose-v2
systemctl enable docker
```

### 2. Создайте .env на сервере

```bash
nano /opt/avatar-bot/.env
```

Содержимое:
```
BOT_TOKEN=your_bot_token
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=google/gemini-2.5-flash-lite
DATABASE_URL=sqlite+aiosqlite:///./data/bot.db
```

### 3. Запустите деплой

```bash
bash deploy/deploy.sh
```

## Управление ботом

```bash
# Проверить статус
ssh root@157.22.180.179 "cd /opt/avatar-bot && docker compose ps"

# Просмотреть логи (в реальном времени)
ssh root@157.22.180.179 "cd /opt/avatar-bot && docker compose logs -f"

# Последние 50 строк логов
ssh root@157.22.180.179 "cd /opt/avatar-bot && docker compose logs --tail=50"

# Перезапустить
ssh root@157.22.180.179 "cd /opt/avatar-bot && docker compose restart"

# Остановить
ssh root@157.22.180.179 "cd /opt/avatar-bot && docker compose down"

# Пересобрать и запустить
ssh root@157.22.180.179 "cd /opt/avatar-bot && docker compose up -d --build"
```

## Обновление

Просто запустите `deploy/deploy.sh` повторно. Скрипт синхронизирует код, пересоберёт образ и перезапустит контейнер.
База данных SQLite хранится в Docker volume `bot-data` и сохраняется между деплоями.

## Откат

Скрипт деплоя использует rsync с флагом `--delete`, поэтому сервер всегда
зеркалирует локальную кодовую базу. Для отката переключитесь на предыдущий
коммит в git локально и повторно запустите `deploy/deploy.sh`.

## Локальный запуск через Docker

```bash
# Создайте .env в корне проекта
cp .env.example .env
# Отредактируйте .env

# Запуск
docker compose up -d --build

# Логи
docker compose logs -f

# Остановка
docker compose down
```
