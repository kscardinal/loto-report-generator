#!/bin/bash

# --- Configuration ---

# Set -e ensures the script exits immediately if a command exits with a non-zero status.
set -e

# --- Color Definitions ---
# Purple/Cyan for general messages
COLOR='\e[95m'
# Green for success
PASS_COLOR='\e[32m'
# Red for errors/failures
FAIL_COLOR='\e[31m'
# Yellow for warnings/skips/no-op
SKIP_COLOR='\e[33m'
# Reset text color
NC='\e[0m'

# --- Counter for Summary ---
STEP_COUNT=1

# --- Error Handling Function (TRAP) ---
# This function runs if the script exits due to an error (non-zero status)
error_handler() {
    # $? holds the exit code of the last executed command
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo -e "\n${FAIL_COLOR}❌ CRITICAL ERROR (Step $STEP_COUNT): Deployment failed! A command exited with code $exit_code.${NC}"
        echo -e "${FAIL_COLOR}Review the logs above for the failing command. Exiting.${NC}"
    fi
}
# Trap the ERR signal (any command failing) and call the error_handler function
trap error_handler ERR

# --- Start of Script ---
echo -e "${COLOR}🚀 Starting intuitive server deployment process...${NC}"
echo "----------------------------------------------------"

# --- STEP 1: Git Pull ---
echo -e "${COLOR}--- $STEP_COUNT. Pulling new changes from GitHub...${NC}"
GIT_OUTPUT=$(git pull 2>&1)
echo "$GIT_OUTPUT"

# Summary Logic for Git Pull
if echo "$GIT_OUTPUT" | grep -q "Already up to date."; then
    echo -e "${SKIP_COLOR}✅ SUMMARY $STEP_COUNT: No new changes found. Already up to date.${NC}"
    # Set a flag to potentially skip later steps if no code changed
    PULL_SUCCESS=false
elif echo "$GIT_OUTPUT" | grep -q "Updating"; then
    echo -e "${PASS_COLOR}🚀 SUMMARY $STEP_COUNT: New code was successfully pulled and merged.${NC}"
    PULL_SUCCESS=true
else
    # This covers other potential outputs like initial clone or branch switching
    echo -e "${SKIP_COLOR}⚠️ SUMMARY $STEP_COUNT: Git pull completed. Check output for specific details.${NC}"
    PULL_SUCCESS=true # Assume success for deployment continuation
fi
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 2: Docker Compose Down ---
echo -e "${COLOR}--- $STEP_COUNT. Bringing down existing services...${NC}"
# Capture output, but 'docker compose down' usually has good, explicit output already
DC_DOWN_OUTPUT=$(docker compose down 2>&1)
echo "$DC_DOWN_OUTPUT"

# Summary Logic for Docker Down
if echo "$DC_DOWN_OUTPUT" | grep -q "No services were started"; then
    echo -e "${SKIP_COLOR}⚠️ SUMMARY $STEP_COUNT: No active services found to stop. Continuing.${NC}"
elif echo "$DC_DOWN_OUTPUT" | grep -q "Stopping" && echo "$DC_DOWN_OUTPUT" | grep -q "Removing"; then
    echo -e "${PASS_COLOR}🛑 SUMMARY $STEP_COUNT: Existing services successfully stopped and removed.${NC}"
else
    # This might happen if 'down' only removes but doesn't stop, or other minor variations
    echo -e "${PASS_COLOR}✅ SUMMARY $STEP_COUNT: Docker services brought down. Check output for details.${NC}"
fi
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 3: Docker Compose Build (Conditional) ---
echo -e "${COLOR}--- $STEP_COUNT. Rebuilding images (this may take a moment)...${NC}"
# Use a spinner/progress indicator for long tasks if possible, but keeping it simple for now.

# The --no-cache flag forces a rebuild, which is good practice for a full deployment.
DC_BUILD_OUTPUT=$(docker compose build --no-cache 2>&1)
echo "$DC_BUILD_OUTPUT"

# Summary Logic for Docker Build
if echo "$DC_BUILD_OUTPUT" | grep -q "Successfully built"; then
    echo -e "${PASS_COLOR}📦 SUMMARY $STEP_COUNT: All required images successfully rebuilt.${NC}"
else
    # While set -e handles actual failures, this catches unexpected success messages
    echo -e "${SKIP_COLOR}⚠️ SUMMARY $STEP_COUNT: Build command ran. Check output for build completion status.${NC}"
fi
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 4: Docker Compose Up ---
echo -e "${COLOR}--- $STEP_COUNT. Starting new application services in detached mode...${NC}"
# The --remove-orphans cleans up containers for services that were removed from the compose file
DC_UP_OUTPUT=$(docker compose up -d --remove-orphans 2>&1)
echo "$DC_UP_OUTPUT"

# Summary Logic for Docker Up
if echo "$DC_UP_OUTPUT" | grep -q "Creating" && echo "$DC_UP_OUTPUT" | grep -q "Done"; then
    echo -e "${PASS_COLOR}✨ SUMMARY $STEP_COUNT: New application services successfully started.${NC}"
elif echo "$DC_UP_OUTPUT" | grep -q "running"; then
    echo -e "${PASS_COLOR}🔁 SUMMARY $STEP_COUNT: Services updated and are running. (Output may vary).${NC}"
else
    echo -e "${FAIL_COLOR}❌ SUMMARY $STEP_COUNT: Services started, but check output for confirmation of all services.${NC}"
fi
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 5: Resource Cleanup: Prune Unused Images ---
echo -e "${COLOR}--- $STEP_COUNT. Cleaning up unused Docker images...${NC}"
IMAGE_PRUNE_OUTPUT=$(docker image prune -f 2>&1)
echo "$IMAGE_PRUNE_OUTPUT"

if echo "$IMAGE_PRUNE_OUTPUT" | grep -q "Total reclaimed space: 0B"; then
    echo -e "${SKIP_COLOR}🧹 SUMMARY $STEP_COUNT: Image prune complete. No space reclaimed.${NC}"
else
    # Extract the reclaimed space amount for a better summary
    RECLAIMED=$(echo "$IMAGE_PRUNE_OUTPUT" | awk '/Total reclaimed space: / {print $4}')
    echo -e "${PASS_COLOR}🧹 SUMMARY $STEP_COUNT: Image prune complete. Reclaimed: ${RECLAIMED}${NC}"
fi
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 6: Resource Cleanup: Prune Build Cache ---
echo -e "${COLOR}--- $STEP_COUNT. Cleaning up unused Docker build cache...${NC}"
BUILDER_PRUNE_OUTPUT=$(docker builder prune --force 2>&1)
echo "$BUILDER_PRUNE_OUTPUT"

if echo "$BUILDER_PRUNE_OUTPUT" | grep -q "Total reclaimed space: 0B"; then
    echo -e "${SKIP_COLOR}🧠 SUMMARY $STEP_COUNT: Builder prune complete. No cache space reclaimed.${NC}"
else
    RECLAIMED=$(echo "$BUILDER_PRUNE_OUTPUT" | awk '/Total reclaimed space: / {print $4}')
    echo -e "${PASS_COLOR}🧠 SUMMARY $STEP_COUNT: Builder prune complete. Reclaimed: ${RECLAIMED}${NC}"
fi
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 7: Resource Cleanup: Full System Prune (Optional/Aggressive Cleanup) ---
echo -e "${COLOR}--- $STEP_COUNT. Performing full system prune (containers, networks, dangling images/volumes)...${NC}"
SYSTEM_PRUNE_OUTPUT=$(docker system prune -f 2>&1)
echo "$SYSTEM_PRUNE_OUTPUT"

if echo "$SYSTEM_PRUNE_OUTPUT" | grep -q "Total reclaimed space: 0B"; then
    echo -e "${SKIP_COLOR}🗑️ SUMMARY $STEP_COUNT: System prune complete. No additional space reclaimed.${NC}"
else
    # The output is complex, but checking for the last line which contains the total is a good heuristic
    RECLAIMED=$(echo "$SYSTEM_PRUNE_OUTPUT" | tail -n 1 | grep "Total reclaimed space" | awk '{print $4}')
    echo -e "${PASS_COLOR}🗑️ SUMMARY $STEP_COUNT: System prune complete. Total reclaimed: ${RECLAIMED}${NC}"
fi
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 8: Wait for Application Startup ---
echo -e "${COLOR}--- $STEP_COUNT. Waiting for application to report successful startup... (Watching logs)${NC}"
# Use 'timeout' in case the log never appears, preventing the script from hanging indefinitely.
# Adjust the timeout value (e.g., 60 seconds) as needed for your application.
STARTUP_WAIT_OUTPUT=$(timeout 60 docker compose logs -f 2>&1 | grep -m 1 "Application startup complete.")
# The exit status of the pipe is complex; check the output directly.
echo "$STARTUP_WAIT_OUTPUT"

if [ -n "$STARTUP_WAIT_OUTPUT" ]; then
    echo -e "${PASS_COLOR}✅ SUMMARY $STEP_COUNT: Application reported successful startup!${NC}"
else
    # Check if grep/timeout failed (timeout is 124)
    if [ $? -eq 124 ]; then
        echo -e "${SKIP_COLOR}⏳ SUMMARY $STEP_COUNT: Application startup message not detected within 60 seconds.${NC}"
        echo -e "${SKIP_COLOR}   Check service logs manually to confirm status: ${COLOR}docker compose logs -f${NC}"
    else
        # Other unexpected failure during log check
        echo -e "${FAIL_COLOR}⚠️ SUMMARY $STEP_COUNT: Log check failed or message was missed. Check output.${NC}"
    fi
fi
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- Final Message ---
echo -e "${PASS_COLOR}🎉 Deployment script finished successfully! ${NC}"
