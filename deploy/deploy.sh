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

echo "==> Building and starting Docker container..."
ssh "$SERVER" "
    cd $REMOTE_DIR
    docker compose up -d --build
    sleep 3
    docker compose ps
    echo '--- Recent logs ---'
    docker compose logs --tail=10
"

echo "==> Deploy complete!"
