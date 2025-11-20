#!/bin/bash
set -e

# Define the color for print statements (Cyan)
COLOR='\e[95m'
# Define the color to reset text back to default
NC='\e[0m' 

echo -e "${COLOR}Starting deployment process...${NC}"
git pull
echo -e "${COLOR}Git pull complete. Bringing down existing services...${NC}"

docker compose down
echo -e "${COLOR}Services stopped. Rebuilding images (this may take a moment)...${NC}"

docker compose build --no-cache
echo -e "${COLOR}Build complete. Starting new services...${NC}"

docker compose up -d --remove-orphans
echo -e "${COLOR}Application services started in detached mode.${NC}"
echo -e "${COLOR}Beginning cleanup of unused Docker resources...${NC}"

echo -e "${COLOR}--- Pruning unused images...${NC}"
docker image prune -f
echo -e "${COLOR}Image prune complete.${NC}"

echo -e "${COLOR}--- Pruning unused build cache...${NC}"
docker builder prune --force
echo -e "${COLOR}Builder prune complete.${NC}"

echo -e "${COLOR}--- Pruning unused volumes...${NC}"
docker volume prune --force
echo -e "${COLOR}Volume prune complete.${NC}"

echo -e "${COLOR}--- Performing full system prune...${NC}"
docker system prune -f
echo -e "${COLOR}System prune complete. Cleanup finished.${NC}"

echo -e "${COLOR}--- Waiting for application to report successful startup...${NC}"
docker compose logs -f 2>&1 | grep -m 1 "Application startup complete."

echo -e "${COLOR}Deployment script finished.${NC}"