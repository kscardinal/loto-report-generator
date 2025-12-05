#!/bin/bash

# =================================================================
# Git Tag Signing Script
# Author: Gemini
# Description:
#   This script converts a list of existing, simple (unsigned) Git 
#   tags into annotated, signed tags using your configured GPG key.
#   It requires user interaction to input the GPG passphrase for 
#   each tag, as Git is invoked repeatedly.
#
# Prerequisite:
# 1. You must have a GPG key configured: 
#    git config --global user.signingkey <YOUR_GPG_KEY_ID>
# 2. You must be on the main branch of your repository.
# 3. All tags in the TAGS_TO_SIGN list must exist locally.
# =================================================================

# -----------------------------------------------------------------
# 1. LIST OF TAGS TO SIGN (MODIFY THIS ARRAY)
# -----------------------------------------------------------------
# Replace the example tags below with the actual names of the 10 
# unsigned tags you want to sign. Separate them with spaces.
TAGS_TO_SIGN=(
    "v0.0.00" 
    "v0.0.00"
)

REMOTE_NAME="origin" # Standard remote name. Change if yours is different.
TAG_MESSAGE_PREFIX="Signed release tag for"

echo "--- Git Tag Signing Utility ---"
echo "Found ${#TAGS_TO_SIGN[@]} tags to process."
echo "Remote target: $REMOTE_NAME"
echo ""

# --- Helper Functions ---

# Function to check if a command exists
command_exists () {
    command -v "$1" >/dev/null 2>&1
}

# Function to check for required Git configuration
check_git_config() {
    if ! git config user.signingkey > /dev/null; then
        echo "❌ Error: Git user.signingkey is not configured."
        echo "Please run: git config --global user.signingkey <YOUR_GPG_KEY_ID>"
        exit 1
    fi
}

# Function to process a single tag
process_tag() {
    local tag_name=$1

    echo "=================================================="
    echo "Processing Tag: $tag_name"
    echo "=================================================="

    # 2. Get the commit hash the current tag points to
    local commit_hash
    commit_hash=$(git rev-list -n 1 "$tag_name" 2>/dev/null)

    if [ -z "$commit_hash" ]; then
        echo "❌ ERROR: Tag '$tag_name' does not exist locally. Skipping."
        return 1
    fi

    echo "Original commit hash found: $commit_hash"

    # 3. Delete the existing unsigned tag (local and remote)
    echo "--> Deleting existing tag locally..."
    if ! git tag -d "$tag_name"; then
        echo "⚠️ WARNING: Could not delete local tag '$tag_name'. Check permissions."
    fi

    echo "--> Deleting existing tag on remote ($REMOTE_NAME)..."
    # Suppress output for deletion if tag doesn't exist on remote, which is fine
    git push "$REMOTE_NAME" :refs/tags/"$tag_name" 2>/dev/null
    
    echo "Successfully removed local and remote references."
    
    # 4. Create the NEW signed tag
    local tag_message="$TAG_MESSAGE_PREFIX $tag_name"
    
    echo "--> Creating new SIGNED tag '$tag_name'..."
    echo "    Message: '$tag_message'"
    
    # The -s option prompts the user for the GPG passphrase
    if git tag -s "$tag_name" "$commit_hash" -m "$tag_message"; then
        echo "✅ New signed tag created successfully."
    else
        echo "❌ ERROR: Failed to create signed tag '$tag_name'."
        echo "This usually happens if the GPG signature fails (e.g., incorrect passphrase or key config)."
        return 1
    fi

    # 5. Push the new signed tag
    echo "--> Pushing new signed tag '$tag_name' to remote ($REMOTE_NAME)..."
    if git push "$REMOTE_NAME" "$tag_name"; then
        echo "✅ Tag '$tag_name' successfully signed and pushed."
    else
        echo "❌ ERROR: Failed to push tag '$tag_name'. Check network connection and remote permissions."
        return 1
    fi

    echo ""
    return 0
}

# --- Main Execution ---

# Pre-checks
check_git_config
if ! command_exists "gpg"; then
    echo "❌ Error: 'gpg' command is not found. Please ensure GPG is installed."
    exit 1
fi

# Loop through the array of tags
for tag in "${TAGS_TO_SIGN[@]}"; do
    process_tag "$tag"
done

echo "--- Tag Signing Process Complete ---"
echo "All listed tags have been processed."
echo "You can verify them now using: git tag -v <tag-name>"