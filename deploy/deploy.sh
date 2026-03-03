#!/bin/bash
set -euo pipefail

SERVER="root@157.22.180.179"
REMOTE_DIR="/opt/avatar-bot"

echo "==> Syncing code to server..."
rsync -avz --delete \
    --exclude '.env' \
    --exclude 'data/' \
    --exclude '.claude/' \
    --exclude '.beads/' \
    --exclude '.serena/' \
    --exclude '.agents/' \
    --exclude '__pycache__/' \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude '*.db' \
    ./ "$SERVER:$REMOTE_DIR/"

echo "==> Installing dependencies on server..."
ssh "$SERVER" "
    cd $REMOTE_DIR
    mkdir -p data
    python3 -m venv .venv 2>/dev/null || true
    .venv/bin/pip install --upgrade pip -q
    .venv/bin/pip install . -q
"

echo "==> Setting up systemd service..."
ssh "$SERVER" "
    cp $REMOTE_DIR/deploy/avatar-bot.service /etc/systemd/system/avatar-bot.service
    systemctl daemon-reload
    systemctl enable avatar-bot
    systemctl restart avatar-bot
    sleep 2
    systemctl status avatar-bot --no-pager || true
"

echo "==> Deploy complete!"
