#!/bin/bash

# --- Configuration ---
set -e

# --- Color Definitions ---
COLOR='\e[95m'
PASS_COLOR='\e[32m'
FAIL_COLOR='\e[31m'
SKIP_COLOR='\e[33m'
TIME_COLOR='\e[94m' # Blue for timing
NC='\e[0m'

# --- Counter for Summary ---
STEP_COUNT=1

# --- Timing Function ---
# Calculates and prints the duration since the start time.
print_duration() {
    local start_time=$1
    local end_time=$(date +%s.%N)
    # Use awk for floating-point math to calculate the difference and format it to 3 decimal places
    local duration=$(awk -v start="$start_time" -v end="$end_time" 'BEGIN {printf "%.3f", end - start}')
    echo -e "${TIME_COLOR}   [Duration: ${duration}s]${NC}"
}

# --- Error Handling Function (TRAP) ---
error_handler() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        # Capture the end time for the failed step
        local end_time=$(date +%s.%N)
        echo -e "\n${FAIL_COLOR}❌ CRITICAL ERROR (Step $STEP_COUNT): Deployment failed! A command exited with code $exit_code.${NC}"
        echo -e "${FAIL_COLOR}Review the logs above for the failing command. Exiting.${NC}"
    fi
}
trap error_handler ERR

# --- Start of Script ---
echo -e "${COLOR}🚀 Starting intuitive server deployment process...${NC}"
echo "----------------------------------------------------"

# --- STEP 1: Git Pull ---
START_TIME_1=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Pulling new changes from GitHub...${NC}"
GIT_OUTPUT=$(git pull 2>&1)
echo "$GIT_OUTPUT"

if echo "$GIT_OUTPUT" | grep -q "Already up to date."; then
    echo -e "${SKIP_COLOR}✅ SUMMARY $STEP_COUNT: No new changes found. Already up to date.${NC}"
elif echo "$GIT_OUTPUT" | grep -q "Updating"; then
    echo -e "${PASS_COLOR}🚀 SUMMARY $STEP_COUNT: New code was successfully pulled and merged.${NC}"
else
    echo -e "${SKIP_COLOR}⚠️ SUMMARY $STEP_COUNT: Git pull completed. Check output for specific details.${NC}"
fi
print_duration $START_TIME_1
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 2: Docker Compose Down ---
START_TIME_2=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Bringing down existing services...${NC}"
DC_DOWN_OUTPUT=$(docker compose down 2>&1)
echo "$DC_DOWN_OUTPUT"

if echo "$DC_DOWN_OUTPUT" | grep -q "No services were started"; then
    echo -e "${SKIP_COLOR}⚠️ SUMMARY $STEP_COUNT: No active services found to stop. Continuing.${NC}"
elif echo "$DC_DOWN_OUTPUT" | grep -q "Stopping" && echo "$DC_DOWN_OUTPUT" | grep -q "Removing"; then
    echo -e "${PASS_COLOR}✅ SUMMARY $STEP_COUNT: Existing services successfully stopped and removed.${NC}"
else
    echo -e "${PASS_COLOR}✅ SUMMARY $STEP_COUNT: Docker services brought down. Check output for details.${NC}"
fi
print_duration $START_TIME_2
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 3: Docker Compose Build ---
START_TIME_3=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Rebuilding images (this may take a moment)...${NC}"

# Capture all output, including the progress and final summary line
DC_BUILD_OUTPUT=$(docker compose build --no-cache 2>&1)
echo "$DC_BUILD_OUTPUT"

# Use a multi-line pattern match to check for the final success line
if echo "$DC_BUILD_OUTPUT" | grep -q 'FINISHED'; then
    
    # Extract the build stage summary (e.g., 12/12) from the last line that contains FINISHED
    BUILD_SUMMARY=$(echo "$DC_BUILD_OUTPUT" | grep 'FINISHED' | tail -n 1 | sed -E 's/.*(\([0-9]+\/[0-9]+\)).*/\1/')
    
    echo -e "${PASS_COLOR}📦 SUMMARY $STEP_COUNT: Images successfully rebuilt ${BUILD_SUMMARY}.${NC}"
else
    # This block executes if the 'set -e' was temporarily disabled or if an error occurred 
    # but the script continued (which shouldn't happen with set -e, but is a safe fallback).
    echo -e "${FAIL_COLOR}❌ SUMMARY $STEP_COUNT: Build FAILED. Review output for error messages.${NC}"
fi

print_duration $START_TIME_3
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 4: Docker Compose Up ---
START_TIME_4=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Starting new application services in detached mode...${NC}"
DC_UP_OUTPUT=$(docker compose up -d --remove-orphans 2>&1)
echo "$DC_UP_OUTPUT"

# 1. Check for the final success line pattern: [+] Running X/Y
# This command extracts the line like "[+] Running 4/4"
RUNNING_STATUS_LINE=$(echo "$DC_UP_OUTPUT" | grep '^\[+\] Running [0-9]\+/[0-9]\+' | tail -n 1)

if [ -n "$RUNNING_STATUS_LINE" ]; then
    
    # 2. Extract the Running count (X) and Total count (Y) from the status line (e.g., 4/4)
    # The output is like "[+] Running 4/4". We isolate the "4/4" part.
    COUNTS=$(echo "$RUNNING_STATUS_LINE" | sed -E 's/.*Running ([0-9]+)\/([0-9]+).*/\1 \2/')
    RUNNING_COUNT=$(echo "$COUNTS" | awk '{print $1}')
    TOTAL_COUNT=$(echo "$COUNTS" | awk '{print $2}')

    # 3. Conditional logic based on counts
    if [ "$RUNNING_COUNT" -eq "$TOTAL_COUNT" ]; then
        echo -e "${PASS_COLOR}✨ SUMMARY $STEP_COUNT: All services successfully started and running (${RUNNING_COUNT}/${TOTAL_COUNT}).${NC}"
    else
        # This catches scenarios like "[+] Running 3/4" which indicate partial failure
        echo -e "${FAIL_COLOR}⚠️ SUMMARY $STEP_COUNT: Partial startup! Running ${RUNNING_COUNT} of ${TOTAL_COUNT} services. Check output.${NC}"
    fi

else
    # This acts as a fallback for older Docker versions or unexpected output formats.
    # We still check for "running" as a general indicator.
    if echo "$DC_UP_OUTPUT" | grep -q "running" || echo "$DC_UP_OUTPUT" | grep -q "Created"; then
        echo -e "${PASS_COLOR}🔁 SUMMARY $STEP_COUNT: Services started/updated (Output format fallback).${NC}"
    else
        echo -e "${FAIL_COLOR}❌ SUMMARY $STEP_COUNT: Service startup FAILED. Review output immediately.${NC}"
    fi
fi

print_duration $START_TIME_4
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 5: Resource Cleanup: Prune Unused Images ---
START_TIME_5=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Cleaning up unused Docker images...${NC}"
IMAGE_PRUNE_OUTPUT=$(docker image prune -f 2>&1)
echo "$IMAGE_PRUNE_OUTPUT"

# Count the number of deleted images by counting lines starting with "deleted:"
DELETED_COUNT=$(echo "$IMAGE_PRUNE_OUTPUT" | grep -c '^deleted:')

if echo "$IMAGE_PRUNE_OUTPUT" | grep -q "Total reclaimed space: 0B"; then
    echo -e "${SKIP_COLOR}🧹 SUMMARY $STEP_COUNT: Image prune complete. No space reclaimed.${NC}"
else
    # Extract the reclaimed space amount
    RECLAIMED=$(echo "$IMAGE_PRUNE_OUTPUT" | awk '/Total reclaimed space: / {print $4}')
    
    # Use the extracted count in the success summary
    echo -e "${PASS_COLOR}🧹 SUMMARY $STEP_COUNT: Image prune complete. ${DELETED_COUNT} images deleted. Reclaimed: ${RECLAIMED}${NC}"
fi

print_duration $START_TIME_5
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 6: Resource Cleanup: Prune Build Cache ---
START_TIME_6=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Cleaning up unused Docker build cache...${NC}"
BUILDER_PRUNE_OUTPUT=$(docker builder prune --force 2>&1)
echo "$BUILDER_PRUNE_OUTPUT"

# Extract the total reclaimed space. We look for the line containing "Total reclaimed space:"
# and take the fourth field, which should contain the size (e.g., 3.257GB)
RECLAIMED=$(echo "$BUILDER_PRUNE_OUTPUT" | awk '/Total reclaimed space: / {print $4}')

# If RECLAIMED is empty, it often means the space was 0B. We check the output for the explicit 0B message.
if echo "$BUILDER_PRUNE_OUTPUT" | grep -q "Total reclaimed space: 0B"; then
    echo -e "${SKIP_COLOR}🧠 SUMMARY $STEP_COUNT: Builder prune complete. No cache space reclaimed.${NC}"
else
    # If the output indicates reclamation, but the extraction failed or returned nothing, 
    # we default to the extracted value.
    if [ -z "$RECLAIMED" ]; then
        # Fallback in case RECLAIMED is empty but space was actually reclaimed (highly unlikely 
        # with standard output, but safer)
        echo -e "${PASS_COLOR}🧠 SUMMARY $STEP_COUNT: Builder prune complete. Space reclaimed. (Check output for size).${NC}"
    else
        echo -e "${PASS_COLOR}🧠 SUMMARY $STEP_COUNT: Builder prune complete. Reclaimed: ${RECLAIMED}${NC}"
    fi
fi

print_duration $START_TIME_6
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 7: Resource Cleanup: Full System Prune ---
START_TIME_7=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Performing full system prune (containers, networks, dangling images/volumes)...${NC}"
SYSTEM_PRUNE_OUTPUT=$(docker system prune -f 2>&1)
echo "$SYSTEM_PRUNE_OUTPUT"

if echo "$SYSTEM_PRUNE_OUTPUT" | grep -q "Total reclaimed space: 0B"; then
    echo -e "${SKIP_COLOR}🗑️ SUMMARY $STEP_COUNT: System prune complete. No additional space reclaimed.${NC}"
else
    RECLAIMED=$(echo "$SYSTEM_PRUNE_OUTPUT" | tail -n 1 | grep "Total reclaimed space" | awk '{print $4}')
    echo -e "${PASS_COLOR}🗑️ SUMMARY $STEP_COUNT: System prune complete. Total reclaimed: ${RECLAIMED}${NC}"
fi
print_duration $START_TIME_7
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 8: Wait for Application Startup ---
START_TIME_8=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Waiting for application to report successful startup... (Watching logs)${NC}"
# Timeout set to 60 seconds
STARTUP_WAIT_OUTPUT=$(timeout 60 docker compose logs -f 2>&1 | grep -m 1 "Application startup complete.")
echo "$STARTUP_WAIT_OUTPUT"

if [ -n "$STARTUP_WAIT_OUTPUT" ]; then
    echo -e "${PASS_COLOR}✅ SUMMARY $STEP_COUNT: Application reported successful startup!${NC}"
else
    if [ $? -eq 124 ]; then
        echo -e "${SKIP_COLOR}⏳ SUMMARY $STEP_COUNT: Application startup message not detected within 60 seconds.${NC}"
        echo -e "${SKIP_COLOR}   Check service logs manually to confirm status: ${COLOR}docker compose logs -f${NC}"
    else
        echo -e "${FAIL_COLOR}⚠️ SUMMARY $STEP_COUNT: Log check failed or message was missed. Check output.${NC}"
    fi
fi
print_duration $START_TIME_8
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- Final Message ---
echo -e "${PASS_COLOR}🎉 Deployment script finished successfully! ${NC}"
