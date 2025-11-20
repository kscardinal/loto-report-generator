#!/bin/bash
set -e

git pull
docker compose down
docker compose build --no-cache
docker compose up -d --remove-orphans

echo "Application started. Beginning cleanup of unused resources..."

docker image prune -f
docker builder prune --force
docker volume prune --force
docker system prune -f

docker compose logs -f 2>&1 | grep -m 1 "Application startup complete."
