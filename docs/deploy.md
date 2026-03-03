# Руководство по деплою

## Требования к серверу

- Linux (рекомендуется Ubuntu 22.04+)
- Python 3.10+
- Доступ по SSH

## Быстрый деплой

```bash
# Из корня проекта на локальной машине:
bash deploy/deploy.sh
```

Скрипт выполнит следующее:
1. Синхронизирует код через rsync (исключая .env, data/, скрытые директории)
2. Создаст виртуальное окружение Python и установит зависимости
3. Настроит systemd-сервис
4. Запустит бота

## Первоначальная настройка сервера

### 1. Создайте .env на сервере

```bash
ssh root@157.22.180.179
nano /opt/avatar-bot/.env
```

Содержимое:
```
BOT_TOKEN=your_bot_token
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=google/gemini-2.5-flash-lite
DATABASE_URL=sqlite+aiosqlite:///./data/bot.db
```

### 2. Создайте директорию для данных

```bash
mkdir -p /opt/avatar-bot/data
```

### 3. Запустите деплой

```bash
bash deploy/deploy.sh
```

## Управление ботом

```bash
# Проверить статус
ssh root@157.22.180.179 "systemctl status avatar-bot"

# Просмотреть логи
ssh root@157.22.180.179 "journalctl -u avatar-bot -f"

# Перезапустить
ssh root@157.22.180.179 "systemctl restart avatar-bot"

# Остановить
ssh root@157.22.180.179 "systemctl stop avatar-bot"
```

## Обновление

Просто запустите `deploy/deploy.sh` повторно. Скрипт синхронизирует код и перезапустит сервис.
База данных SQLite в директории `data/` сохраняется между деплоями.

## Откат

Скрипт деплоя использует rsync с флагом `--delete`, поэтому сервер всегда
зеркалирует локальную кодовую базу. Для отката переключитесь на предыдущий
коммит в git локально и повторно запустите `deploy/deploy.sh`.
