#!/bin/bash

# --- Configuration ---
set -e

# --- Color Definitions ---
COLOR='\e[95m'
PASS_COLOR='\e[32m'
FAIL_COLOR='\e[31m'
SKIP_COLOR='\e[33m'
TIME_COLOR='\e[34m'
NC='\e[0m'

# --- Counter for Summary ---
STEP_COUNT=1

# --- Timing Function (MODIFIED) ---
# Calculates and prints the duration since the start time WITHOUT a trailing newline.
print_duration() {
    local start_time=$1
    local end_time=$(date +%s.%N)
    # Use awk for floating-point math to calculate the difference and format it to 3 decimal places
    local duration=$(awk -v start="$start_time" -v end="$end_time" 'BEGIN {printf "%.3f", end - start}')
    # Added -n to suppress the trailing newline
    echo -e "${TIME_COLOR}   [Duration: ${duration}s]${NC}"
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
START_TIME_0=$(date +%s.%N)
echo -e "${COLOR}🚀 Starting intuitive server deployment process...${NC}"
echo "----------------------------------------------------"

# --- STEP 1: Git Pull ---
START_TIME_1=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Pulling new changes from GitHub...${NC}"
GIT_OUTPUT=$(git pull 2>&1)

if echo "$GIT_OUTPUT" | grep -q "Already up to date."; then
    # Used $() for inline printing
    echo -e "${SKIP_COLOR}✅ SUMMARY $STEP_COUNT: No new changes found. Already up to date.${NC}"
elif echo "$GIT_OUTPUT" | grep -q "Updating"; then
    # Used $() for inline printing
    echo -e "${PASS_COLOR}🚀 SUMMARY $STEP_COUNT: New code was successfully pulled and merged.${NC}"
else
    # Used $() for inline printing
    echo -e "${SKIP_COLOR}⚠️ SUMMARY $STEP_COUNT: Git pull completed. Check output for specific details.${NC}"
fi
print_duration $START_TIME_1
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 2: Docker Compose Down ---
START_TIME_2=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Bringing down existing services...${NC}"

# Capture output quietly without echoing it to the screen
DC_DOWN_OUTPUT=$(docker compose -f docker-compose.yml -f docker-compose.prod.yml down 2>&1)

# Initialize counters
STOPPED_COUNT=0
REMOVED_COUNT=0
TOTAL_COUNT=0

# Extract unique container names that were processed (stopped or removed)
CONTAINER_NAMES=$(echo "$DC_DOWN_OUTPUT" | grep -E '(Container)' | awk '{print $2}' | sort -u)

# Loop through each container name found
for NAME in $CONTAINER_NAMES; do
    # Skip non-container names like 'Network' or empty strings
    if [[ "$NAME" == "Network" || -z "$NAME" ]]; then
        continue
    fi
    
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    STATUS=""
    
    # Check if the container was stopped
    if echo "$DC_DOWN_OUTPUT" | grep -q "Container $NAME  Stopped"; then
        STATUS+="stopped"
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    fi
    
    # Check if the container was removed
    if echo "$DC_DOWN_OUTPUT" | grep -q "Container $NAME  Removed"; then
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

# Summary Logic
if [ $TOTAL_COUNT -eq 0 ]; then
    echo -e "${SKIP_COLOR}⚠️ SUMMARY $STEP_COUNT: No active services found to stop. Continuing.${NC}"
elif [ $STOPPED_COUNT -eq $TOTAL_COUNT ] && [ $REMOVED_COUNT -eq $TOTAL_COUNT ]; then
    echo -e "${PASS_COLOR}✔ SUMMARY $STEP_COUNT: All ${TOTAL_COUNT} services stopped and removed (${STOPPED_COUNT}/${TOTAL_COUNT} stopped, ${REMOVED_COUNT}/${TOTAL_COUNT} removed).${NC}"
else
    # Changed to FAIL_COLOR since a partial shutdown is usually an issue
    echo -e "${FAIL_COLOR}🛑 SUMMARY $STEP_COUNT: Partial shutdown. Check output for details (${STOPPED_COUNT}/${TOTAL_COUNT} stopped, ${REMOVED_COUNT}/${TOTAL_COUNT} removed).${NC}"
fi
print_duration $START_TIME_2
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 3: Docker Compose Build ---
START_TIME_3=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Rebuilding images (this may take a moment)...${NC}"
DC_BUILD_OUTPUT=$(docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache 2>&1)

# Do NOT echo output here if it was already echoed earlier in the script logic.
# If you didn't echo it, uncomment the next line:
# echo "$DC_BUILD_OUTPUT"

# Check for the final success line: DONE on the exporting step (#11 DONE 29.7s)
if echo "$DC_BUILD_OUTPUT" | grep -q '^#11 DONE'; then
    
    # Extract the final build stage summary from a line like: [+] Building 41.6s (12/12) FINISHED
    # (Using the pattern from the previous request for robustness, even if not explicitly in your final output)
    BUILD_SUMMARY=$(echo "$DC_BUILD_OUTPUT" | grep 'FINISHED' | tail -n 1 | sed -E 's/.*(\([0-9]+\/[0-9]+\)).*/\1/')
    
    # Use a simpler message if the count extraction fails
    if [ -z "$BUILD_SUMMARY" ]; then
        BUILD_SUMMARY="successfully"
    fi
    
    # Used $() for inline printing
    echo -e "${PASS_COLOR}📦 SUMMARY $STEP_COUNT: Images ${BUILD_SUMMARY} rebuilt.${NC}"
else
    # This block executes if the build command fails to report a final DONE.
    # Used $() for inline printing
    echo -e "${FAIL_COLOR}❌ SUMMARY $STEP_COUNT: Build FAILED. Review output for error messages.${NC}"
fi
print_duration $START_TIME_3
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 4: Docker Compose Up ---
START_TIME_4=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Starting new application services in detached mode...${NC}"

# Capture output quietly
DC_UP_OUTPUT=$(docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans 2>&1)

# Initialize counters
CREATED_COUNT=0
STARTED_COUNT=0
TOTAL_COUNT=0

# Extract unique container names that were processed (created or started)
CONTAINER_NAMES=$(echo "$DC_UP_OUTPUT" | grep -E 'Container .* Created|Container .* Starting|Container .* Started' | awk '{print $2}' | sort -u)

# Loop through each container name found
for NAME in $CONTAINER_NAMES; do
    # Skip non-container names like 'Network' or empty strings
    if [[ "$NAME" == "Network" || -z "$NAME" ]]; then
        continue
    fi
    
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    STATUS=""
    
    # Check if the container was created
    if echo "$DC_UP_OUTPUT" | grep -q "Container $NAME  Created"; then
        STATUS+="created"
        CREATED_COUNT=$((CREATED_COUNT + 1))
    fi
    
    # Check if the container was started
    if echo "$DC_UP_OUTPUT" | grep -q "Container $NAME  Started"; then
        if [ -n "$STATUS" ]; then
            STATUS+=" and "
        fi
        STATUS+="started"
        STARTED_COUNT=$((STARTED_COUNT + 1))
    fi

    # Print the custom status line
    if [ -n "$STATUS" ]; then
        echo -e "${PASS_COLOR}    ✔ $NAME - $STATUS${NC}"
    fi
done

# Summary Logic
if [ $TOTAL_COUNT -eq 0 ]; then
    echo -e "${FAIL_COLOR}🛑 SUMMARY $STEP_COUNT: Service startup FAILED. No containers processed. Review logs.${NC}"
elif [ $CREATED_COUNT -eq $TOTAL_COUNT ] && [ $STARTED_COUNT -eq $TOTAL_COUNT ]; then
    echo -e "${PASS_COLOR}✔ SUMMARY $STEP_COUNT: All ${TOTAL_COUNT} services created and started (${CREATED_COUNT}/${TOTAL_COUNT} created, ${STARTED_COUNT}/${TOTAL_COUNT} started).${NC}"
else
    echo -e "${SKIP_COLOR}⚠️ SUMMARY $STEP_COUNT: Partial startup. Check output for details (${CREATED_COUNT}/${TOTAL_COUNT} created, ${STARTED_COUNT}/${TOTAL_COUNT} started).${NC}"
fi
print_duration $START_TIME_4
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 5: Resource Cleanup: Prune Unused Images ---
START_TIME_5=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Cleaning up unused Docker images...${NC}"
IMAGE_PRUNE_OUTPUT=$(docker image prune -f 2>&1)

# Count the number of deleted images by counting lines starting with "sha256:" 
# that follow "Deleted Images:" (since the output format is slightly variable)
# A safer count is checking for the 'sha256:' keyword on its own line after the header.
DELETED_COUNT=$(echo "$IMAGE_PRUNE_OUTPUT" | grep -c 'sha256:')

# Your output showed Total reclaimed space: 0B, so we prioritize the deleted count
if [ "$DELETED_COUNT" -gt 0 ]; then
    # Extract the reclaimed space amount (will be 0B in this specific case, but still extracted)
    RECLAIMED=$(echo "$IMAGE_PRUNE_OUTPUT" | awk '/Total reclaimed space: / {print $4}')
    
    # Use the extracted count in the success summary, and $() for inline printing
    echo -e "${PASS_COLOR}🧹 SUMMARY $STEP_COUNT: Image prune complete. ${DELETED_COUNT} image(s) deleted. Reclaimed: ${RECLAIMED}.${NC}"
else
    # Used $() for inline printing
    echo -e "${SKIP_COLOR}🧹 SUMMARY $STEP_COUNT: Image prune complete. No space reclaimed.${NC}"
fi
print_duration $START_TIME_5
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 6: Resource Cleanup: Prune Build Cache ---
START_TIME_6=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Cleaning up unused Docker build cache...${NC}"
BUILDER_PRUNE_OUTPUT=$(docker builder prune --force 2>&1)

# Extract the total reclaimed space from the "Total: [size]" line
# This looks for the line starting with "Total:" and prints the second field (the size)
RECLAIMED=$(echo "$BUILDER_PRUNE_OUTPUT" | awk '/^Total:/ {print $2}' | tail -n 1)

# Check if RECLAIMED is empty, which implies nothing was reclaimed
if [ -z "$RECLAIMED" ]; then
    # Used $() for inline printing
    echo -e "${SKIP_COLOR}🧠 SUMMARY $STEP_COUNT: Builder prune complete. No cache space reclaimed.${NC}"
else
    # Used $() for inline printing
    echo -e "${PASS_COLOR}🧠 SUMMARY $STEP_COUNT: Builder prune complete. Reclaimed: ${RECLAIMED}.${NC}"
fi
print_duration $START_TIME_6
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 7: Resource Cleanup: Full System Prune ---
START_TIME_7=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Performing full system prune (containers, networks, dangling images/volumes)...${NC}"
SYSTEM_PRUNE_OUTPUT=$(docker system prune -f 2>&1)

if echo "$SYSTEM_PRUNE_OUTPUT" | grep -q "Total reclaimed space: 0B"; then
    # Used $() for inline printing
    echo -e "${SKIP_COLOR}🗑️ SUMMARY $STEP_COUNT: System prune complete. No additional space reclaimed.${NC}"
else
    RECLAIMED=$(echo "$SYSTEM_PRUNE_OUTPUT" | tail -n 1 | grep "Total reclaimed space" | awk '{print $4}')
    # Used $() for inline printing
    echo -e "${PASS_COLOR}🗑️ SUMMARY $STEP_COUNT: System prune complete. Total reclaimed: ${RECLAIMED}.${NC}"
fi
print_duration $START_TIME_7
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 8: Wait for Application Startup ---
START_TIME_8=$(date +%s.%N)
echo -e "${COLOR}--- $STEP_COUNT. Waiting for application to report successful startup... (Watching logs)${NC}"
# Timeout set to 60 seconds
STARTUP_WAIT_OUTPUT=$(timeout 60 docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f 2>&1 | grep -m 1 "Application startup complete.")
echo "$STARTUP_WAIT_OUTPUT"

if [ -n "$STARTUP_WAIT_OUTPUT" ]; then
    echo -e "${PASS_COLOR}✔ SUMMARY $STEP_COUNT: Application reported successful startup!${NC}"
else
    if [ $? -eq 124 ]; then
        # Used $() for inline printing
        echo -e "${SKIP_COLOR}⏳ SUMMARY $STEP_COUNT: Application startup message not detected within 60 seconds.${NC}"
        echo -e "${SKIP_COLOR}   Check service logs manually to confirm status: ${COLOR}docker compose logs -f${NC}"
    else
        # Used $() for inline printing
        echo -e "${FAIL_COLOR}⚠️ SUMMARY $STEP_COUNT: Log check failed or message was missed. Check output.${NC}"
    fi
fi
print_duration $START_TIME_8
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- STEP 9: Install Root Crontab ---
START_TIME_9=$(date +%s.%N)
CRON_FILE="cron.host" # Assumes cron.host is in the main folder

echo -e "${COLOR}--- $STEP_COUNT. Installing ${CRON_FILE} as root crontab (with safety check)...${NC}"

# Check if the local cron file exists
if [ ! -f "$CRON_FILE" ]; then
    echo -e "${FAIL_COLOR}❌ SUMMARY $STEP_COUNT: Crontab file ${CRON_FILE} not found! Skipping cron setup.${NC}"
    print_duration $START_TIME_9
    STEP_COUNT=$((STEP_COUNT + 1))
    echo "----------------------------------------------------"
    return # Use 'return' or 'exit 0' depending on whether you want to stop the script entirely
fi

# 1. Create a temporary file with the currently installed root crontab, excluding comments/blanks.
#    We use mktemp to ensure a unique, safe file.
TEMP_CURRENT_CRON=$(mktemp)

echo "--- DEBUG: Attempting to read root crontab into $TEMP_CURRENT_CRON ---" 
# Filter out blank lines and lines starting with '#' (comments)
# Sudo is needed to read the root crontab
sudo crontab -u root -l 2>/dev/null | grep -v '^[[:space:]]*#' | grep -v '^[[:space:]]*$' > "$TEMP_CURRENT_CRON"
# If the script prints the line below, the read was successful.
echo "--- DEBUG: Successfully read root crontab. ---" 

CURRENT_CRON_LINES=$(wc -l < "$TEMP_CURRENT_CRON")

# 2. Create a temporary file with the content of the deployment file, excluding comments/blanks.
TEMP_HOST_CRON=$(mktemp)

echo "--- DEBUG: Attempting to read cron.host into $TEMP_HOST_CRON ---"
grep -v '^[[:space:]]*#' "$CRON_FILE" | grep -v '^[[:space:]]*$' > "$TEMP_HOST_CRON"
echo "--- DEBUG: Successfully read cron.host. ---"

# 3. Check for differences and potential data loss (i.e., extra lines in the current crontab)

# Check if the files are exactly the same (0 lines of diff means they are identical)
if diff -q "$TEMP_CURRENT_CRON" "$TEMP_HOST_CRON" > /dev/null; then
    # CRONTABS ARE IDENTICAL: Skip installation
    echo -e "${SKIP_COLOR}📜 SUMMARY $STEP_COUNT: Root crontab is already set correctly. Skipping installation.${NC}"
elif [ "$CURRENT_CRON_LINES" -gt "$HOST_CRON_LINES" ]; then
    # CURRENT CRONTAB HAS EXTRA LINES: Potential data loss (non-managed jobs exist)
    echo -e "${SKIP_COLOR}⚠️ SUMMARY $STEP_COUNT: Existing root crontab has ${CURRENT_CRON_LINES} active lines, but ${CRON_FILE} only has ${HOST_CRON_LINES}.${NC}"
    echo -e "${SKIP_COLOR}   **WARNING**: Installing ${CRON_FILE} would **remove** existing root cron jobs not defined in the file. Skipping overwrite.${NC}"
else
    # CURRENT CRONTAB IS EMPTY, OR HAS FEWER LINES THAN THE HOST FILE (SAFE TO OVERWRITE/ADD)
    # The overwrite is required to update time/path if the content has changed
    echo "Current and deployment crontab content differs. Installing new crontab..."
    CRONTAB_OUTPUT=$(sudo crontab -u root "$CRON_FILE" 2>&1)

    if [ $? -eq 0 ]; then
        echo -e "${PASS_COLOR}📜 SUMMARY $STEP_COUNT: New cron job successfully installed/updated for root user.${NC}"
    else
        echo -e "${FAIL_COLOR}❌ SUMMARY $STEP_COUNT: Cron job installation FAILED. Output: ${CRONTAB_OUTPUT}${NC}"
    fi
fi

# Cleanup temporary files
rm -f "$TEMP_CURRENT_CRON" "$TEMP_HOST_CRON"

print_duration $START_TIME_9
STEP_COUNT=$((STEP_COUNT + 1))
echo "----------------------------------------------------"

# --- Final Message ---
echo -e "${PASS_COLOR}🎉 Deployment script finished successfully!${NC}"
print_duration $START_TIME_0