#!/bin/bash
set -e

git pull
docker compose down
docker compose build --no-cache
docker compose up -d --remove-orphans
docker image prune -f
