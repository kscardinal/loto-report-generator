#!/bin/bash

# ==============================================================================
# DEPLOYMENT SCRIPT: Intuitive Server Deployment (Production)
# This script automates Git pull, Docker Compose down/build/up, and resource cleanup.
# ==============================================================================

# --- Configuration ---
# Exit immediately if a command exits with a non-zero status.
set -e

# --- Color Definitions ---
COLOR='\e[95m'  # Purple for step titles
PASS_COLOR='\e[32m' # Green for success
FAIL_COLOR='\e[31m' # Red for errors
SKIP_COLOR='\e[33m' # Yellow for skipped actions/warnings
TIME_COLOR='\e[34m' # Blue for timing info
NC='\e[0m' # No Color reset

# --- Counter for Summary ---
STEP_COUNT=1

# --- Timing Function ---
# Calculates duration and prints start/end timestamps for a step.
# Args: $1=start_time_precise, $2=start_time_formatted
print_duration() {
    local start_time_precise=$1
    local start_time_formatted=$2
    local end_time_precise=$(date +%s.%N)
    local end_time_formatted=$(date +%H:%M:%S)
    
    # Use awk for floating-point math to calculate the difference
    local duration=$(awk -v start="$start_time_precise" -v end="$end_time_precise" 'BEGIN {printf "%.3f", end - start}')
    
    echo -e "${TIME_COLOR}   [Duration: ${duration}s] [${start_time_formatted}-${end_time_formatted}]${NC}"
}

# --- Error Handling Function (TRAP) ---
error_handler() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo -e "\n${FAIL_COLOR}🛑 CRITICAL ERROR (Step $STEP_COUNT): Deployment failed! A command exited with code $exit_code.${NC}"
        echo -e "${FAIL_COLOR}Review the logs above for the failing command. Exiting.${NC}"
    fi
}
# Trap ERR ensures error_handler is called on any non-zero exit code.
trap error_handler ERR

# --- Start of Script ---
START_TIME_0=$(date +%s.%N)
START_TIME_0_F=$(date +%H:%M:%S)
echo -e "${COLOR}🚀 Starting intuitive server deployment process...${NC}"
echo "----------------------------------------------------"

# --- STEP 1: Git Pull ---
START_TIME_1=$(date +%s.%N)
START_TIME_1_F=$(date +%H:%M:%S)
echo -e "${COLOR}--- $STEP_COUNT. Pulling new changes from GitHub...${NC}"
GIT_OUTPUT=$(git pull 2>&1)

### Summary Logic: Check Git output for status
if echo "$GIT_OUTPUT" | grep -q "Already up to date."; then
    echo -e "${SKIP_COLOR}⚠️  SUMMARY $STEP_COUNT: No new changes found. Already up to date.${NC}"
elif echo "$GIT_OUTPUT" | grep -q "Updating"; then
    echo -e "${PASS_COLOR}🚀 SUMMARY $STEP_COUNT: New code was successfully pulled and merged.${NC}"
else
    echo -e "${SKIP_COLOR}⚠️  SUMMARY $STEP_COUNT: Git pull completed. Check output for specific details.${NC}"
fi
print_duration $START_TIME_1 $START_TIME_1_F
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 2: Docker Compose Down ---
START_TIME_2=$(date +%s.%N)
START_TIME_2_F=$(date +%H:%M:%S)
echo -e "${COLOR}--- $STEP_COUNT. Bringing down existing services...${NC}"

# Capture output quietly
DC_DOWN_OUTPUT=$(docker compose -f docker-compose.yml -f docker-compose.prod.yml down 2>&1)
echo "$DC_DOWN_OUTPUT"

# Initialize counters
STOPPED_COUNT=0
REMOVED_COUNT=0
TOTAL_COUNT=0

# Extract unique container names that were processed
CONTAINER_NAMES=$(echo "$DC_DOWN_OUTPUT" | grep 'Container.*Removed' | awk '{print $2}' | sort -u)

### Loop through containers to determine status
for NAME in $CONTAINER_NAMES; do
    # Skip non-container names
    if [[ "$NAME" == "Network" || -z "$NAME" ]]; then
        continue
    fi
    
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    STATUS=""
    
    # Check if the container was stopped
    if echo "$DC_DOWN_OUTPUT" | grep -q "Container $NAME  Stopped"; then
        STATUS+="stopped"
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    fi
    
    # Check if the container was removed
    if echo "$DC_DOWN_OUTPUT" | grep -q "Container $NAME  Removed"; then
        if [ -n "$STATUS" ]; then
            STATUS+=" and "
        fi
        STATUS+="removed"
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
    fi

    # Print the custom status line
    if [ -n "$STATUS" ]; then
        echo -e "${PASS_COLOR}    ✔ $NAME - $STATUS${NC}"
    fi
done

### Summary Logic
if [ $TOTAL_COUNT -eq 0 ]; then
    echo -e "${SKIP_COLOR}⚠️  SUMMARY $STEP_COUNT: No active services found to stop. Continuing.${NC}"
elif [ $STOPPED_COUNT -eq $TOTAL_COUNT ] && [ $REMOVED_COUNT -eq $TOTAL_COUNT ]; then
    echo -e "${PASS_COLOR}🧹 SUMMARY $STEP_COUNT: All ${TOTAL_COUNT} services stopped and removed (${STOPPED_COUNT}/${TOTAL_COUNT} stopped, ${REMOVED_COUNT}/${TOTAL_COUNT} removed).${NC}"
else
    # Partial shutdown is treated as a critical issue.
    echo -e "${FAIL_COLOR}🛑 SUMMARY $STEP_COUNT: Partial shutdown. Check output for details (${STOPPED_COUNT}/${TOTAL_COUNT} stopped, ${REMOVED_COUNT}/${TOTAL_COUNT} removed).${NC}"
fi
print_duration $START_TIME_2 $START_TIME_2_F
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 3: Docker Compose Build ---
START_TIME_3=$(date +%s.%N)
START_TIME_3_F=$(date +%H:%M:%S)
echo -e "${COLOR}--- $STEP_COUNT. Rebuilding images (this may take a moment)...${NC}"
DC_BUILD_OUTPUT=$(docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache 2>&1)

### Summary Logic: Check for successful build export
# Check for the final success line: DONE on the exporting step
if echo "$DC_BUILD_OUTPUT" | grep -q '^#11 DONE'; then
    
    # Extract the build summary if available
    BUILD_SUMMARY=$(echo "$DC_BUILD_OUTPUT" | grep 'FINISHED' | tail -n 1 | sed -E 's/.*(\([0-9]+\/[0-9]+\)).*/\1/')
    
    if [ -z "$BUILD_SUMMARY" ]; then
        BUILD_SUMMARY="successfully"
    fi
    
    echo -e "${PASS_COLOR}📦 SUMMARY $STEP_COUNT: Images ${BUILD_SUMMARY} rebuilt.${NC}"
else
    # This block executes if the build command fails to report a final DONE.
    echo -e "${FAIL_COLOR}🛑 SUMMARY $STEP_COUNT: Build FAILED. Review output for error messages.${NC}"
fi
print_duration $START_TIME_3 $START_TIME_3_F
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 4: Docker Compose Up ---
START_TIME_4=$(date +%s.%N)
START_TIME_4_F=$(date +%H:%M:%S)
echo -e "${COLOR}--- $STEP_COUNT. Starting new application services in detached mode...${NC}"

# Capture output quietly
DC_UP_OUTPUT=$(docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans 2>&1)
echo "$DC_UP_OUTPUT"

# Initialize counters
CREATED_COUNT=0
STARTED_COUNT=0
TOTAL_COUNT=0

# Extract unique container names that were processed
CONTAINER_NAMES=$(echo "$DC_UP_OUTPUT" | grep 'Container.*Started' | awk '{print $3}' | sort -u)

### Loop through containers to determine status
for NAME in $CONTAINER_NAMES; do
    # Skip non-container names
    if [[ "$NAME" == "Network" || -z "$NAME" ]]; then
        continue
    fi
    
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    STATUS=""
    
    # Check if the container was created
    if echo "$DC_UP_OUTPUT" | grep -q "Container $NAME  Created"; then
        STATUS+="created"
        CREATED_COUNT=$((CREATED_COUNT + 1))
    fi
    
    # Check if the container was started
    if echo "$DC_UP_OUTPUT" | grep -q "Container $NAME  Started"; then
        if [ -n "$STATUS" ]; then
            STATUS+=" and "
        fi
        STATUS+="started"
        STARTED_COUNT=$((STARTED_COUNT + 1))
    fi

    # Print the custom status line
    if [ -n "$STATUS" ]; then
        echo -e "${PASS_COLOR}    ✔ $NAME - $STATUS${NC}"
    fi
done

### Summary Logic
if [ $TOTAL_COUNT -eq 0 ]; then
    echo -e "${FAIL_COLOR}🛑 SUMMARY $STEP_COUNT: Service startup FAILED. No containers processed. Review logs.${NC}"
elif [ $CREATED_COUNT -eq $TOTAL_COUNT ] && [ $STARTED_COUNT -eq $TOTAL_COUNT ]; then
    echo -e "${PASS_COLOR}🏁 SUMMARY $STEP_COUNT: All ${TOTAL_COUNT} services created and started (${CREATED_COUNT}/${TOTAL_COUNT} created, ${STARTED_COUNT}/${TOTAL_COUNT} started).${NC}"
else
    echo -e "${SKIP_COLOR}⚠️  SUMMARY $STEP_COUNT: Partial startup. Check output for details (${CREATED_COUNT}/${TOTAL_COUNT} created, ${STARTED_COUNT}/${TOTAL_COUNT} started).${NC}"
fi
print_duration $START_TIME_4 $START_TIME_4_F
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 5: Resource Cleanup: Prune Unused Images ---
START_TIME_5=$(date +%s.%N)
START_TIME_5_F=$(date +%H:%M:%S)
echo -e "${COLOR}--- $STEP_COUNT. Cleaning up unused Docker images...${NC}"
IMAGE_PRUNE_OUTPUT=$(docker image prune -f 2>&1)

# Count deleted images by checking for 'sha256:' output lines.
DELETED_COUNT=$(echo "$IMAGE_PRUNE_OUTPUT" | grep -c 'sha256:')

### Summary Logic
if [ "$DELETED_COUNT" -gt 0 ]; then
    # Extract the reclaimed space amount
    RECLAIMED=$(echo "$IMAGE_PRUNE_OUTPUT" | awk '/Total reclaimed space: / {print $4}')
    
    echo -e "${PASS_COLOR}🧹 SUMMARY $STEP_COUNT: Image prune complete. ${DELETED_COUNT} image(s) deleted. Reclaimed: ${RECLAIMED}.${NC}"
else
    echo -e "${SKIP_COLOR}🧹 SUMMARY $STEP_COUNT: Image prune complete. No space reclaimed.${NC}"
fi
print_duration $START_TIME_5 $START_TIME_5_F
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 6: Resource Cleanup: Prune Build Cache ---
START_TIME_6=$(date +%s.%N)
START_TIME_6_F=$(date +%H:%M:%S)
echo -e "${COLOR}--- $STEP_COUNT. Cleaning up unused Docker build cache...${NC}"
BUILDER_PRUNE_OUTPUT=$(docker builder prune --force 2>&1)

# Extract the total reclaimed space from the final summary line.
RECLAIMED=$(echo "$BUILDER_PRUNE_OUTPUT" | awk '/^Total:/ {print $2}' | tail -n 1)

### Summary Logic
if [ -z "$RECLAIMED" ]; then
    echo -e "${SKIP_COLOR}🧠 SUMMARY $STEP_COUNT: Builder prune complete. No cache space reclaimed.${NC}"
else
    echo -e "${PASS_COLOR}🧠 SUMMARY $STEP_COUNT: Builder prune complete. Reclaimed: ${RECLAIMED}.${NC}"
fi
print_duration $START_TIME_6 $START_TIME_6_F
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 7: Resource Cleanup: Full System Prune ---
START_TIME_7=$(date +%s.%N)
START_TIME_7_F=$(date +%H:%M:%S)
echo -e "${COLOR}--- $STEP_COUNT. Performing full system prune (containers, networks, dangling images/volumes)...${NC}"
SYSTEM_PRUNE_OUTPUT=$(docker system prune -f 2>&1)

### Summary Logic
if echo "$SYSTEM_PRUNE_OUTPUT" | grep -q "Total reclaimed space: 0B"; then
    echo -e "${SKIP_COLOR}⚠️  SUMMARY $STEP_COUNT: System prune complete. No additional space reclaimed.${NC}"
else
    # Extract the total reclaimed space
    RECLAIMED=$(echo "$SYSTEM_PRUNE_OUTPUT" | tail -n 1 | grep "Total reclaimed space" | awk '{print $4}')
    echo -e "${PASS_COLOR}🗑️  SUMMARY $STEP_COUNT: System prune complete. Total reclaimed: ${RECLAIMED}.${NC}"
fi
print_duration $START_TIME_7 $START_TIME_7_F
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 8: Wait for Application Startup ---
START_TIME_8=$(date +%s.%N)
START_TIME_8_F=$(date +%H:%M:%S)
echo -e "${COLOR}--- $STEP_COUNT. Waiting for application to report successful startup... (Watching logs)${NC}"

# Wait up to 60 seconds for the application startup message.
STARTUP_WAIT_OUTPUT=$(timeout 60 docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f 2>&1 | grep -m 1 "Application startup complete.")
echo "$STARTUP_WAIT_OUTPUT"

### Summary Logic
if [ -n "$STARTUP_WAIT_OUTPUT" ]; then
    echo -e "${PASS_COLOR}✅ SUMMARY $STEP_COUNT: Application reported successful startup!${NC}"
else
    if [ $? -eq 124 ]; then
        # Timeout occurred (exit code 124)
        echo -e "${SKIP_COLOR}⚠️  SUMMARY $STEP_COUNT: Application startup message not detected within 60 seconds.${NC}"
        echo -e "${SKIP_COLOR}   Check service logs manually to confirm status: ${COLOR}docker compose logs -f${NC}"
    else
        # Log check failed for another reason
        echo -e "${FAIL_COLOR}🛑 SUMMARY $STEP_COUNT: Log check failed or message was missed. Check output.${NC}"
    fi
fi
print_duration $START_TIME_8 $START_TIME_8_F
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 9: Install Crontab (Current User) ---
START_TIME_9=$(date +%s.%N)
START_TIME_9_F=$(date +%H:%M:%S)
CRON_FILE="cron.host" # Assumes cron.host is in the main folder

echo -e "${COLOR}--- $STEP_COUNT. Installing ${CRON_FILE} (Overwrite Mode)${NC}"

# Check if the local cron file exists
if [ ! -f "$CRON_FILE" ]; then
    echo -e "${FAIL_COLOR}❌ SUMMARY $STEP_COUNT: Crontab file ${CRON_FILE} not found! Skipping cron setup.${NC}"
else
    # Install the file as the current user's crontab. This is a full overwrite.
    CRONTAB_OUTPUT=$(crontab "$CRON_FILE" 2>&1)

    if [ $? -eq 0 ]; then
        # Check if the cron file actually has content to report success more accurately
        if grep -q '[^[:space:]]' "$CRON_FILE"; then
            echo -e "${PASS_COLOR}📜 SUMMARY $STEP_COUNT: New cron job(s) from ${CRON_FILE} successfully installed (full overwrite).${NC}"
        else
            echo -e "${SKIP_COLOR}📜 SUMMARY $STEP_COUNT: Crontab cleared. ${CRON_FILE} contains no active jobs.${NC}"
        fi
    else
        # This usually means a syntax error in cron.host or a system issue
        echo -e "${FAIL_COLOR}❌ SUMMARY $STEP_COUNT: Crontab installation FAILED (Exit Code 1). Output: ${CRONTAB_OUTPUT}${NC}"
    fi
fi

print_duration $START_TIME_9 $START_TIME_9_F
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- Final Message ---
echo -e "${PASS_COLOR}🎉 Deployment script finished successfully!${NC}"
print_duration $START_TIME_0 $START_TIME_0_F